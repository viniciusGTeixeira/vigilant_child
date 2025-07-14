"""
Analyzer para análise de horários e conformidade com rotinas de trabalho
Integra com PostgreSQL para dados de horários e rotinas
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz
from typing import Dict, Any, List, Optional, Tuple
import json
import re
import torch
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from .base_analyzer import BaseAnalyzer


class ScheduleAnalyzer(BaseAnalyzer):
    """
    Analyzer especializado em análise de horários e conformidade
    
    Funcionalidades:
    - Verificação de conformidade com horários de trabalho
    - Detecção de funcionários fora do horário
    - Análise de padrões de entrada/saída
    - Comparação com rotinas esperadas
    - Identificação de anomalias temporais
    - Análise de permanência em áreas
    """
    
    def __init__(self, config: Dict[str, Any], device: torch.device):
        super().__init__(config, device)
        self.timezone = pytz.timezone(config.get('timezone', 'America/Sao_Paulo'))
        
        # Configurações específicas para horários
        self.schedule_config = config.get('analyzers', {}).get('schedule', {
            'tolerance_minutes': 15,
            'break_duration_max': 90,  # minutos
            'overtime_threshold': 480,  # minutos (8 horas)
            'early_arrival_threshold': 30,  # minutos antes do horário
            'late_departure_threshold': 30,  # minutos após horário
            'weekend_work_alert': True,
            'holiday_work_alert': True
        })
        
        # Configuração do PostgreSQL
        db_config = config.get('database', {})
        self.db_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        self.engine = sa.create_engine(
            self.db_url,
            pool_size=db_config.get('pool_size', 10),
            max_overflow=db_config.get('max_overflow', 20),
            pool_timeout=db_config.get('pool_timeout', 30),
            pool_recycle=db_config.get('pool_recycle', 1800),
            echo=db_config.get('echo', False)
        )
        self.Session = sessionmaker(bind=self.engine)
        
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        ScheduleAnalyzer não usa modelo ML, mas precisa conectar ao banco
        """
        try:
            # Testar conexão com o banco
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Erro ao conectar ao PostgreSQL: {e}")
            self.is_loaded = False
            return False
    
    def analyze(self, image: torch.Tensor, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analisa conformidade com horários baseado em metadados
        """
        if not metadata or not self.is_loaded:
            return {'error': 'Metadados ausentes ou analyzer não inicializado'}
            
        detection_time = metadata.get('detection_time', datetime.now())
        employee_info = metadata.get('employee_info', {})
        location = metadata.get('location')
        
        results = self.analyze_schedule_compliance(detection_time, employee_info, location)
        
        # Adicionar resultados ao banco
        self._save_analysis_results(results)
        
        return self.postprocess_results(results)
    
    def get_confidence_threshold(self) -> float:
        """
        Retorna limiar de confiança para análise temporal
        """
        return 1.0 - (self.schedule_config['tolerance_minutes'] / (24 * 60))
    
    def _save_analysis_results(self, results: Dict[str, Any]) -> None:
        """
        Salva resultados da análise no PostgreSQL
        """
        try:
            with self.Session() as session:
                # Criar query de inserção
                query = text("""
                    INSERT INTO schedule_analysis (
                        timestamp, employee_id, location, compliance_status,
                        expected_status, current_status, schedule_match,
                        risk_level, anomalies
                    ) VALUES (
                        :timestamp, :employee_id, :location, :compliance_status,
                        :expected_status, :current_status, :schedule_match,
                        :risk_level, :anomalies
                    )
                """)
                
                # Preparar dados
                params = {
                    'timestamp': results['timestamp'],
                    'employee_id': results.get('employee_info', {}).get('id'),
                    'location': results.get('location'),
                    'compliance_status': results['compliance_status'],
                    'expected_status': results['expected_status'],
                    'current_status': results['current_status'],
                    'schedule_match': results['schedule_match'],
                    'risk_level': results['risk_level'],
                    'anomalies': json.dumps(results['anomalies'])
                }
                
                # Executar inserção
                session.execute(query, params)
                session.commit()
                
        except Exception as e:
            print(f"Erro ao salvar resultados no PostgreSQL: {e}")
    
    def load_data(self) -> bool:
        """
        Carrega dados de horários e rotinas do PostgreSQL
        """
        try:
            with self.Session() as session:
                # Carregar horários
                schedules = session.execute(text("""
                    SELECT * FROM employee_schedules 
                    WHERE active = true
                    ORDER BY updated_at DESC
                """))
                self.schedule_data = pd.DataFrame(schedules)
                
                # Carregar rotinas
                routines = session.execute(text("""
                    SELECT * FROM work_routines
                    WHERE active = true
                    ORDER BY priority DESC
                """))
                self.routines_data = pd.DataFrame(routines)
                
                return True
                
        except Exception as e:
            print(f"Erro ao carregar dados do PostgreSQL: {e}")
            return False
    
    def analyze_schedule_compliance(self, detection_time: datetime, 
                                  employee_info: Dict[str, Any] = None,
                                  location: str = None) -> Dict[str, Any]:
        """
        Analisa conformidade com horários de trabalho
        """
        results = {
            'timestamp': detection_time.isoformat(),
            'compliance_status': 'unknown',
            'expected_status': 'unknown',
            'current_status': 'present',
            'schedule_match': False,
            'anomalies': [],
            'schedule_info': {},
            'risk_level': 'low'
        }
        
        try:
            # Obter informações de horário para o funcionário/área
            schedule_info = self._get_schedule_info(employee_info, location)
            results['schedule_info'] = schedule_info
            
            if schedule_info:
                # Verificar status esperado no momento atual
                expected_status = self._get_expected_status(detection_time, schedule_info)
                results['expected_status'] = expected_status
                
                # Comparar com presença detectada
                compliance = self._check_compliance(detection_time, expected_status, schedule_info)
                results.update(compliance)
                
                # Detectar anomalias específicas
                anomalies = self._detect_schedule_anomalies(detection_time, schedule_info, employee_info)
                results['anomalies'] = anomalies
                
                # Calcular nível de risco
                results['risk_level'] = self._calculate_risk_level(results)
            
        except Exception as e:
            print(f"Erro na análise de horários: {e}")
            results['error'] = str(e)
        
        return results
    
    def _get_schedule_info(self, employee_info: Dict[str, Any] = None, 
                          location: str = None) -> Dict[str, Any]:
        """
        Obtém informações de horário relevantes do PostgreSQL
        """
        schedule_info = {}
        
        try:
            with self.Session() as session:
                # Construir query base
                query = """
                    SELECT es.*, g.name as grade_name, g.description
                    FROM employee_schedules es
                    JOIN schedule_grades g ON es.grade_id = g.id
                    WHERE es.active = true
                """
                params = {}
                
                # Adicionar filtros
                if location:
                    query += " AND g.location = :location"
                    params['location'] = location
                    
                if employee_info and 'id' in employee_info:
                    query += " AND (es.employee_id = :employee_id OR es.grade_id IN (SELECT grade_id FROM employee_grades WHERE employee_id = :employee_id))"
                    params['employee_id'] = employee_info['id']
                
                # Executar query
                results = session.execute(text(query), params)
                
                # Processar resultados
                for row in results:
                    grade = row.grade_name
                    schedule_info[grade] = {
                        'grade': grade,
                        'description': row.description,
                        'parsed_schedule': self._parse_schedule_text(row.schedule_text),
                        'raw_text': row.schedule_text,
                        'messages': row.messages or '',
                        'location': row.location,
                        'priority': row.priority
                    }
            
        except Exception as e:
            print(f"Erro ao obter informações de horário do PostgreSQL: {e}")
        
        return schedule_info
    
    def _parse_schedule_text(self, schedule_text: str) -> Dict[str, Any]:
        """
        Analisa texto de horário e extrai informações estruturadas
        """
        parsed = {
            'weekdays': {},
            'saturday': {},
            'sunday': {},
            'holidays': {},
            'special_dates': {},
            'is_24h': False
        }
        
        try:
            # Verificar se é operação 24h
            if '24' in schedule_text and 'hora' in schedule_text.lower():
                parsed['is_24h'] = True
                parsed['weekdays'] = {'start': '00:00', 'end': '23:59'}
                parsed['saturday'] = {'start': '00:00', 'end': '23:59'}
                parsed['sunday'] = {'start': '00:00', 'end': '23:59'}
                return parsed
            
            # Patterns para extração de horários
            time_pattern = r'(\d{1,2}):(\d{2})'
            
            # Extrair horários para dias úteis
            weekday_match = re.search(
                r'(?:segunda|seg|úteis?).*?(\d{1,2}:\d{2}).*?(\d{1,2}:\d{2})', 
                schedule_text, re.IGNORECASE
            )
            if weekday_match:
                parsed['weekdays'] = {
                    'start': weekday_match.group(1),
                    'end': weekday_match.group(2)
                }
            
            # Extrair horários para sábado
            saturday_match = re.search(
                r'sábado.*?(\d{1,2}:\d{2}).*?(\d{1,2}:\d{2})', 
                schedule_text, re.IGNORECASE
            )
            if saturday_match:
                parsed['saturday'] = {
                    'start': saturday_match.group(1),
                    'end': saturday_match.group(2)
                }
            
            # Extrair horários para domingo
            sunday_match = re.search(
                r'domingo.*?(\d{1,2}:\d{2}).*?(\d{1,2}:\d{2})', 
                schedule_text, re.IGNORECASE
            )
            if sunday_match:
                parsed['sunday'] = {
                    'start': sunday_match.group(1),
                    'end': sunday_match.group(2)
                }
            
            # Verificar datas especiais (ex: 24/12)
            special_date_pattern = r'(\d{1,2}/\d{1,2}).*?(\d{1,2}:\d{2}).*?(\d{1,2}:\d{2})'
            special_matches = re.findall(special_date_pattern, schedule_text)
            
            for date_str, start_time, end_time in special_matches:
                parsed['special_dates'][date_str] = {
                    'start': start_time,
                    'end': end_time
                }
            
        except Exception as e:
            print(f"Erro no parsing de horário: {e}")
        
        return parsed
    
    def _get_expected_status(self, check_time: datetime, schedule_info: Dict[str, Any]) -> str:
        """
        Determina status esperado do funcionário no momento especificado
        """
        try:
            # Converter para timezone local
            local_time = check_time.astimezone(self.timezone)
            
            # Para cada grade/horário, verificar se deveria estar trabalhando
            for grade, info in schedule_info.items():
                parsed_schedule = info['parsed_schedule']
                
                # Verificar se é horário de trabalho
                if self._is_work_time(local_time, parsed_schedule):
                    return 'should_be_present'
            
            # Se não encontrou nenhum horário ativo
            return 'should_be_absent'
            
        except Exception as e:
            print(f"Erro ao determinar status esperado: {e}")
            return 'unknown'
    
    def _is_work_time(self, check_time: datetime, schedule: Dict[str, Any]) -> bool:
        """
        Verifica se um horário específico está dentro do expediente
        """
        try:
            # Se é operação 24h
            if schedule.get('is_24h', False):
                return True
            
            # Obter dia da semana (0 = segunda, 6 = domingo)
            weekday = check_time.weekday()
            current_time = check_time.time()
            current_date = check_time.date()
            
            # Verificar datas especiais primeiro
            date_str = current_date.strftime('%d/%m')
            if date_str in schedule.get('special_dates', {}):
                special_schedule = schedule['special_dates'][date_str]
                return self._time_in_range(current_time, special_schedule)
            
            # Verificar por dia da semana
            if weekday < 5:  # Segunda a sexta
                weekday_schedule = schedule.get('weekdays', {})
                if weekday_schedule:
                    return self._time_in_range(current_time, weekday_schedule)
            elif weekday == 5:  # Sábado
                saturday_schedule = schedule.get('saturday', {})
                if saturday_schedule:
                    return self._time_in_range(current_time, saturday_schedule)
            elif weekday == 6:  # Domingo
                sunday_schedule = schedule.get('sunday', {})
                if sunday_schedule:
                    return self._time_in_range(current_time, sunday_schedule)
            
            return False
            
        except Exception as e:
            print(f"Erro ao verificar horário de trabalho: {e}")
            return False
    
    def _time_in_range(self, check_time: time, schedule: Dict[str, str]) -> bool:
        """
        Verifica se um horário está dentro do range especificado
        """
        try:
            if 'start' not in schedule or 'end' not in schedule:
                return False
            
            start_time = datetime.strptime(schedule['start'], '%H:%M').time()
            end_time = datetime.strptime(schedule['end'], '%H:%M').time()
            
            # Verificar se o horário está no range
            if start_time <= end_time:
                # Mesmo dia
                return start_time <= check_time <= end_time
            else:
                # Atravessa meia-noite
                return check_time >= start_time or check_time <= end_time
                
        except Exception as e:
            print(f"Erro ao verificar range de horário: {e}")
            return False
    
    def _check_compliance(self, detection_time: datetime, expected_status: str, 
                         schedule_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica conformidade com horários e registra no banco
        """
        results = {
            'compliance_status': 'unknown',
            'schedule_match': False,
            'deviation_minutes': 0,
            'details': {}
        }
        
        try:
            with self.Session() as session:
                # Registrar verificação
                query = text("""
                    INSERT INTO schedule_checks (
                        timestamp, expected_status, actual_status,
                        location, employee_id, deviation_minutes
                    ) VALUES (
                        :timestamp, :expected_status, :actual_status,
                        :location, :employee_id, :deviation_minutes
                    ) RETURNING id
                """)
                
                deviation = self._calculate_time_deviation(detection_time, schedule_info)
                
                params = {
                    'timestamp': detection_time,
                    'expected_status': expected_status,
                    'actual_status': 'present',
                    'location': next(iter(schedule_info.values()))['location'] if schedule_info else None,
                    'employee_id': None,  # TODO: Adicionar ID do funcionário
                    'deviation_minutes': deviation
                }
                
                check_id = session.execute(query, params).scalar()
                session.commit()
                
                # Determinar status de conformidade
                if expected_status == 'should_be_present':
                    results['compliance_status'] = 'compliant'
                    results['schedule_match'] = True
                elif expected_status == 'should_be_absent':
                    results['compliance_status'] = 'non_compliant'
                    results['schedule_match'] = False
                
                results['deviation_minutes'] = deviation
                results['check_id'] = check_id
                
        except Exception as e:
            print(f"Erro ao verificar conformidade: {e}")
            results['error'] = str(e)
        
        return results
    
    def _calculate_time_deviation(self, detection_time: datetime, 
                                 schedule_info: Dict[str, Any]) -> int:
        """
        Calcula desvio em minutos do horário esperado
        """
        try:
            local_time = detection_time.astimezone(self.timezone)
            min_deviation = float('inf')
            
            # Para cada horário, calcular a menor distância
            for grade, info in schedule_info.items():
                schedule = info['parsed_schedule']
                
                # Verificar distância até próximo horário de trabalho
                deviation = self._calculate_deviation_to_schedule(local_time, schedule)
                min_deviation = min(min_deviation, deviation)
            
            return int(min_deviation) if min_deviation != float('inf') else 0
            
        except Exception as e:
            print(f"Erro ao calcular desvio: {e}")
            return 0
    
    def _calculate_deviation_to_schedule(self, check_time: datetime, 
                                       schedule: Dict[str, Any]) -> float:
        """
        Calcula desvio em minutos até o próximo horário válido
        """
        try:
            current_time = check_time.time()
            weekday = check_time.weekday()
            
            # Lista de horários possíveis para verificar
            schedules_to_check = []
            
            # Adicionar horário do dia atual
            if weekday < 5 and 'weekdays' in schedule:
                schedules_to_check.append(schedule['weekdays'])
            elif weekday == 5 and 'saturday' in schedule:
                schedules_to_check.append(schedule['saturday'])
            elif weekday == 6 and 'sunday' in schedule:
                schedules_to_check.append(schedule['sunday'])
            
            min_deviation = float('inf')
            
            for sched in schedules_to_check:
                if 'start' in sched and 'end' in sched:
                    start_time = datetime.strptime(sched['start'], '%H:%M').time()
                    end_time = datetime.strptime(sched['end'], '%H:%M').time()
                    
                    # Calcular distância até início ou fim do expediente
                    start_minutes = self._time_difference_minutes(current_time, start_time)
                    end_minutes = self._time_difference_minutes(current_time, end_time)
                    
                    min_deviation = min(min_deviation, abs(start_minutes), abs(end_minutes))
            
            return min_deviation
            
        except Exception as e:
            print(f"Erro ao calcular desvio para horário: {e}")
            return 0.0
    
    def _time_difference_minutes(self, time1: time, time2: time) -> float:
        """
        Calcula diferença em minutos entre dois horários
        """
        # Converter para minutos desde meia-noite
        minutes1 = time1.hour * 60 + time1.minute
        minutes2 = time2.hour * 60 + time2.minute
        
        return minutes2 - minutes1
    
    def _detect_schedule_anomalies(self, detection_time: datetime, 
                                  schedule_info: Dict[str, Any],
                                  employee_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Detecta e registra anomalias de horário
        """
        anomalies = []
        
        try:
            # Verificar cada tipo de anomalia
            early_arrival = self._check_early_arrival(detection_time, schedule_info)
            if early_arrival:
                anomalies.append(early_arrival)
                self._save_anomaly(early_arrival, employee_info)
            
            late_departure = self._check_late_departure(detection_time, schedule_info)
            if late_departure:
                anomalies.append(late_departure)
                self._save_anomaly(late_departure, employee_info)
            
            weekend_work = self._check_weekend_work(detection_time, schedule_info)
            if weekend_work:
                anomalies.append(weekend_work)
                self._save_anomaly(weekend_work, employee_info)
            
            holiday_work = self._check_holiday_work(detection_time)
            if holiday_work:
                anomalies.append(holiday_work)
                self._save_anomaly(holiday_work, employee_info)
            
            lunch_anomaly = self._check_lunch_time_anomaly(detection_time)
            if lunch_anomaly:
                anomalies.append(lunch_anomaly)
                self._save_anomaly(lunch_anomaly, employee_info)
            
        except Exception as e:
            print(f"Erro ao detectar anomalias: {e}")
            anomalies.append({
                'type': 'error',
                'description': f'Erro na detecção de anomalias: {e}',
                'severity': 'high'
            })
        
        return anomalies

    def _save_anomaly(self, anomaly: Dict[str, Any], 
                      employee_info: Dict[str, Any] = None) -> None:
        """
        Salva anomalia detectada no PostgreSQL
        """
        try:
            with self.Session() as session:
                query = text("""
                    INSERT INTO schedule_anomalies (
                        timestamp, type, description, severity,
                        employee_id, location, details
                    ) VALUES (
                        :timestamp, :type, :description, :severity,
                        :employee_id, :location, :details
                    )
                """)
                
                params = {
                    'timestamp': datetime.now(),
                    'type': anomaly['type'],
                    'description': anomaly['description'],
                    'severity': anomaly['severity'],
                    'employee_id': employee_info.get('id') if employee_info else None,
                    'location': anomaly.get('location'),
                    'details': json.dumps(anomaly.get('details', {}))
                }
                
                session.execute(query, params)
                session.commit()
                
        except Exception as e:
            print(f"Erro ao salvar anomalia: {e}")
    
    def _check_early_arrival(self, check_time: datetime, 
                           schedule_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verifica chegada muito cedo e registra no banco
        """
        try:
            local_time = check_time.astimezone(self.timezone)
            threshold = self.schedule_config['early_arrival_threshold']
            
            for grade_info in schedule_info.values():
                schedule = grade_info['parsed_schedule']
                
                if schedule['is_24h']:
                    continue
                
                # Verificar horário de entrada
                if 'weekdays' in schedule and local_time.weekday() < 5:
                    start_time = datetime.strptime(schedule['weekdays']['start'], '%H:%M').time()
                elif 'saturday' in schedule and local_time.weekday() == 5:
                    start_time = datetime.strptime(schedule['saturday']['start'], '%H:%M').time()
                elif 'sunday' in schedule and local_time.weekday() == 6:
                    start_time = datetime.strptime(schedule['sunday']['start'], '%H:%M').time()
                else:
                    continue
                
                # Calcular diferença em minutos
                arrival_time = local_time.time()
                minutes_early = self._time_difference_minutes(start_time, arrival_time)
                
                if minutes_early > threshold:
                    return {
                        'type': 'early_arrival',
                        'description': f'Chegada {minutes_early} minutos antes do horário',
                        'severity': 'low' if minutes_early < threshold * 2 else 'medium',
                        'details': {
                            'minutes_early': minutes_early,
                            'expected_time': start_time.strftime('%H:%M'),
                            'actual_time': arrival_time.strftime('%H:%M'),
                            'grade': grade_info['grade'],
                            'location': grade_info['location']
                        }
                    }
            
        except Exception as e:
            print(f"Erro ao verificar chegada antecipada: {e}")
        
        return None

    def _check_late_departure(self, check_time: datetime, 
                            schedule_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verifica saída muito tarde e registra no banco
        """
        try:
            local_time = check_time.astimezone(self.timezone)
            threshold = self.schedule_config['late_departure_threshold']
            
            for grade_info in schedule_info.values():
                schedule = grade_info['parsed_schedule']
                
                if schedule['is_24h']:
                    continue
                
                # Verificar horário de saída
                if 'weekdays' in schedule and local_time.weekday() < 5:
                    end_time = datetime.strptime(schedule['weekdays']['end'], '%H:%M').time()
                elif 'saturday' in schedule and local_time.weekday() == 5:
                    end_time = datetime.strptime(schedule['saturday']['end'], '%H:%M').time()
                elif 'sunday' in schedule and local_time.weekday() == 6:
                    end_time = datetime.strptime(schedule['sunday']['end'], '%H:%M').time()
                else:
                    continue
                
                # Calcular diferença em minutos
                departure_time = local_time.time()
                minutes_late = self._time_difference_minutes(end_time, departure_time)
                
                if minutes_late > threshold:
                    return {
                        'type': 'late_departure',
                        'description': f'Saída {minutes_late} minutos após o horário',
                        'severity': 'low' if minutes_late < threshold * 2 else 'medium',
                        'details': {
                            'minutes_late': minutes_late,
                            'expected_time': end_time.strftime('%H:%M'),
                            'actual_time': departure_time.strftime('%H:%M'),
                            'grade': grade_info['grade'],
                            'location': grade_info['location']
                        }
                    }
            
        except Exception as e:
            print(f"Erro ao verificar saída tardia: {e}")
        
        return None

    def _check_weekend_work(self, check_time: datetime, 
                          schedule_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verifica trabalho em fim de semana e registra no banco
        """
        if not self.schedule_config['weekend_work_alert']:
            return None
            
        try:
            local_time = check_time.astimezone(self.timezone)
            
            # Verificar se é fim de semana
            if local_time.weekday() >= 5:
                for grade_info in schedule_info.values():
                    schedule = grade_info['parsed_schedule']
                    
                    # Se tem horário definido para o dia, não é anomalia
                    if local_time.weekday() == 5 and 'saturday' in schedule:
                        continue
                    if local_time.weekday() == 6 and 'sunday' in schedule:
                        continue
                    
                    return {
                        'type': 'weekend_work',
                        'description': f'Trabalho em {"sábado" if local_time.weekday() == 5 else "domingo"}',
                        'severity': 'medium',
                        'details': {
                            'weekday': local_time.weekday(),
                            'time': local_time.strftime('%H:%M'),
                            'grade': grade_info['grade'],
                            'location': grade_info['location']
                        }
                    }
            
        except Exception as e:
            print(f"Erro ao verificar trabalho em fim de semana: {e}")
        
        return None

    def _check_holiday_work(self, check_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Verifica trabalho em feriado consultando banco de dados
        """
        if not self.schedule_config['holiday_work_alert']:
            return None
            
        try:
            local_time = check_time.astimezone(self.timezone)
            
            with self.Session() as session:
                # Verificar se é feriado
                query = text("""
                    SELECT name, type, description
                    FROM holidays
                    WHERE date = :date
                    AND (location IS NULL OR location = :location)
                """)
                
                params = {
                    'date': local_time.date(),
                    'location': None  # TODO: Adicionar localização
                }
                
                holiday = session.execute(query, params).fetchone()
                
                if holiday:
                    return {
                        'type': 'holiday_work',
                        'description': f'Trabalho em feriado: {holiday.name}',
                        'severity': 'high',
                        'details': {
                            'holiday_name': holiday.name,
                            'holiday_type': holiday.type,
                            'holiday_description': holiday.description,
                            'time': local_time.strftime('%H:%M')
                        }
                    }
            
        except Exception as e:
            print(f"Erro ao verificar trabalho em feriado: {e}")
        
        return None

    def _check_lunch_time_anomaly(self, check_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Verifica anomalias no horário de almoço consultando histórico
        """
        try:
            local_time = check_time.astimezone(self.timezone)
            
            # Verificar se está no período típico de almoço (11h-15h)
            if 11 <= local_time.hour <= 15:
                with self.Session() as session:
                    # Buscar padrão histórico
                    query = text("""
                        SELECT 
                            AVG(EXTRACT(HOUR FROM timestamp) * 60 + 
                                EXTRACT(MINUTE FROM timestamp)) as avg_lunch_time,
                            STDDEV(EXTRACT(HOUR FROM timestamp) * 60 + 
                                  EXTRACT(MINUTE FROM timestamp)) as stddev_lunch_time
                        FROM schedule_checks
                        WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 11 AND 15
                        AND employee_id = :employee_id
                        AND timestamp > CURRENT_DATE - INTERVAL '30 days'
                    """)
                    
                    params = {
                        'employee_id': None  # TODO: Adicionar ID do funcionário
                    }
                    
                    stats = session.execute(query, params).fetchone()
                    
                    if stats and stats.avg_lunch_time and stats.stddev_lunch_time:
                        current_minutes = local_time.hour * 60 + local_time.minute
                        deviation = abs(current_minutes - stats.avg_lunch_time)
                        
                        # Se desvio > 2 desvios padrão
                        if deviation > 2 * stats.stddev_lunch_time:
                            return {
                                'type': 'lunch_time_anomaly',
                                'description': 'Horário de almoço atípico',
                                'severity': 'low',
                                'details': {
                                    'usual_time': f"{int(stats.avg_lunch_time // 60):02d}:{int(stats.avg_lunch_time % 60):02d}",
                                    'current_time': local_time.strftime('%H:%M'),
                                    'deviation_minutes': int(deviation)
                                }
                            }
            
        except Exception as e:
            print(f"Erro ao verificar anomalia no horário de almoço: {e}")
        
        return None

    def _calculate_risk_level(self, results: Dict[str, Any]) -> str:
        """
        Calcula nível de risco baseado em histórico de anomalias
        """
        try:
            with self.Session() as session:
                # Buscar histórico recente de anomalias
                query = text("""
                    SELECT 
                        COUNT(*) as total_anomalies,
                        COUNT(*) FILTER (WHERE severity = 'high') as high_severity,
                        COUNT(*) FILTER (WHERE severity = 'medium') as medium_severity,
                        COUNT(*) FILTER (WHERE type = :current_type) as same_type_count
                    FROM schedule_anomalies
                    WHERE timestamp > CURRENT_DATE - INTERVAL '7 days'
                    AND employee_id = :employee_id
                """)
                
                params = {
                    'employee_id': results.get('employee_info', {}).get('id'),
                    'current_type': results.get('anomalies', [{}])[0].get('type') if results.get('anomalies') else None
                }
                
                stats = session.execute(query, params).fetchone()
                
                if stats:
                    # Calcular score de risco
                    risk_score = (
                        stats.high_severity * 3 +
                        stats.medium_severity * 2 +
                        stats.same_type_count
                    )
                    
                    # Determinar nível baseado no score
                    if risk_score > 10:
                        return 'high'
                    elif risk_score > 5:
                        return 'medium'
                    else:
                        return 'low'
            
        except Exception as e:
            print(f"Erro ao calcular nível de risco: {e}")
        
        return 'unknown'
    
    def get_schedule_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera resumo legível da análise de horários
        """
        summary = {}
        
        compliance_status = results.get('compliance_status', 'unknown')
        if compliance_status == 'compliant':
            summary['status'] = '✅ Dentro do horário de trabalho'
        elif compliance_status == 'violation':
            violation_type = results.get('violation_type', 'unknown')
            if violation_type == 'unauthorized_presence':
                summary['status'] = '❌ Presença fora do horário autorizado'
            else:
                summary['status'] = '❌ Violação de horário'
        else:
            summary['status'] = '⚠️ Status de horário indefinido'
        
        # Resumo de anomalias
        anomalies = results.get('anomalies', [])
        if anomalies:
            high_severity = sum(1 for a in anomalies if a.get('severity') == 'high')
            if high_severity > 0:
                summary['anomalies'] = f'🚨 {high_severity} anomalia(s) crítica(s)'
            else:
                summary['anomalies'] = f'⚠️ {len(anomalies)} anomalia(s) detectada(s)'
        else:
            summary['anomalies'] = '✅ Nenhuma anomalia detectada'
        
        # Nível de risco
        risk_level = results.get('risk_level', 'low')
        risk_icons = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🟠',
            'critical': '🔴'
        }
        summary['risk'] = f"{risk_icons.get(risk_level, '⚪')} Risco {risk_level}"
        
        return summary 