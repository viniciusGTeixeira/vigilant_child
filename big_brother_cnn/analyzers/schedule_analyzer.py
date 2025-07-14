"""
Analyzer para análise de horários e conformidade com rotinas de trabalho
Integra com dados de horários CSV e rotinas JSON
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz
from typing import Dict, Any, List, Optional, Tuple
import json
import re

from .base_analyzer import BaseAnalyzer


class ScheduleAnalyzer:
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
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.schedule_data = None
        self.routines_data = None
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
        
    def load_data(self, horarios_path: str, rotinas_path: str) -> bool:
        """
        Carrega dados de horários e rotinas
        """
        try:
            # Carregar horários
            self.schedule_data = pd.read_csv(horarios_path)
            print(f"Carregados {len(self.schedule_data)} registros de horários")
            
            # Carregar rotinas
            with open(rotinas_path, 'r', encoding='utf-8') as f:
                self.routines_data = json.load(f)
            print(f"Carregadas {len(self.routines_data.get('rotinas', {}))} rotinas")
            
            return True
            
        except Exception as e:
            print(f"Erro ao carregar dados de horários: {e}")
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
        Obtém informações de horário relevantes
        """
        schedule_info = {}
        
        try:
            if self.schedule_data is None:
                return schedule_info
            
            # Filtrar por localização se disponível
            relevant_schedules = self.schedule_data.copy()
            
            if location:
                # Tentar encontrar grade correspondente à localização
                location_matches = relevant_schedules[
                    relevant_schedules['Grade'].str.contains(location, case=False, na=False)
                ]
                if len(location_matches) > 0:
                    relevant_schedules = location_matches
            
            # Se há informação do funcionário, tentar encontrar horário específico
            if employee_info and 'name' in employee_info:
                # Placeholder: implementar lógica de mapeamento funcionário -> grade
                pass
            
            # Processar horários encontrados
            for _, row in relevant_schedules.iterrows():
                grade = row['Grade']
                schedule_text = row['Horário Funcionamento']
                
                parsed_schedule = self._parse_schedule_text(schedule_text)
                
                schedule_info[grade] = {
                    'raw_text': schedule_text,
                    'parsed_schedule': parsed_schedule,
                    'messages': row.get('Mensagem', ''),
                    'grade': grade
                }
            
        except Exception as e:
            print(f"Erro ao obter informações de horário: {e}")
        
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
        Verifica conformidade com horário esperado
        """
        compliance = {
            'compliance_status': 'compliant',
            'schedule_match': True,
            'violation_type': None,
            'deviation_minutes': 0
        }
        
        try:
            if expected_status == 'should_be_present':
                # Funcionário deveria estar presente e está
                compliance['compliance_status'] = 'compliant'
                compliance['schedule_match'] = True
                
            elif expected_status == 'should_be_absent':
                # Funcionário não deveria estar presente mas está
                compliance['compliance_status'] = 'violation'
                compliance['schedule_match'] = False
                compliance['violation_type'] = 'unauthorized_presence'
                
                # Calcular quanto tempo fora do horário
                deviation = self._calculate_time_deviation(detection_time, schedule_info)
                compliance['deviation_minutes'] = deviation
                
            else:
                compliance['compliance_status'] = 'unknown'
                compliance['schedule_match'] = False
            
        except Exception as e:
            print(f"Erro ao verificar conformidade: {e}")
            compliance['compliance_status'] = 'error'
        
        return compliance
    
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
        Detecta anomalias específicas nos horários
        """
        anomalies = []
        
        try:
            local_time = detection_time.astimezone(self.timezone)
            
            # Verificar chegada muito cedo
            early_arrival = self._check_early_arrival(local_time, schedule_info)
            if early_arrival:
                anomalies.append(early_arrival)
            
            # Verificar saída muito tarde
            late_departure = self._check_late_departure(local_time, schedule_info)
            if late_departure:
                anomalies.append(late_departure)
            
            # Verificar trabalho em fim de semana
            if self.schedule_config['weekend_work_alert']:
                weekend_work = self._check_weekend_work(local_time, schedule_info)
                if weekend_work:
                    anomalies.append(weekend_work)
            
            # Verificar trabalho em feriado
            if self.schedule_config['holiday_work_alert']:
                holiday_work = self._check_holiday_work(local_time)
                if holiday_work:
                    anomalies.append(holiday_work)
            
            # Verificar horário de almoço atípico
            lunch_anomaly = self._check_lunch_time_anomaly(local_time)
            if lunch_anomaly:
                anomalies.append(lunch_anomaly)
            
        except Exception as e:
            print(f"Erro ao detectar anomalias: {e}")
        
        return anomalies
    
    def _check_early_arrival(self, check_time: datetime, 
                           schedule_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verifica chegada muito cedo
        """
        try:
            threshold = self.schedule_config['early_arrival_threshold']
            
            for grade, info in schedule_info.items():
                schedule = info['parsed_schedule']
                weekday = check_time.weekday()
                
                # Obter horário de início esperado
                expected_start = None
                if weekday < 5 and 'weekdays' in schedule:
                    expected_start = schedule['weekdays'].get('start')
                elif weekday == 5 and 'saturday' in schedule:
                    expected_start = schedule['saturday'].get('start')
                elif weekday == 6 and 'sunday' in schedule:
                    expected_start = schedule['sunday'].get('start')
                
                if expected_start:
                    start_time = datetime.strptime(expected_start, '%H:%M').time()
                    current_time = check_time.time()
                    
                    # Calcular diferença
                    diff_minutes = self._time_difference_minutes(current_time, start_time)
                    
                    if diff_minutes < -threshold:  # Chegou muito cedo
                        return {
                            'type': 'early_arrival',
                            'severity': 'medium',
                            'description': f'Chegada {abs(diff_minutes):.0f} minutos antes do horário',
                            'expected_time': expected_start,
                            'actual_time': current_time.strftime('%H:%M'),
                            'grade': grade
                        }
            
        except Exception as e:
            print(f"Erro ao verificar chegada cedo: {e}")
        
        return None
    
    def _check_late_departure(self, check_time: datetime, 
                            schedule_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verifica saída muito tarde
        """
        try:
            threshold = self.schedule_config['late_departure_threshold']
            
            for grade, info in schedule_info.items():
                schedule = info['parsed_schedule']
                weekday = check_time.weekday()
                
                # Obter horário de fim esperado
                expected_end = None
                if weekday < 5 and 'weekdays' in schedule:
                    expected_end = schedule['weekdays'].get('end')
                elif weekday == 5 and 'saturday' in schedule:
                    expected_end = schedule['saturday'].get('end')
                elif weekday == 6 and 'sunday' in schedule:
                    expected_end = schedule['sunday'].get('end')
                
                if expected_end:
                    end_time = datetime.strptime(expected_end, '%H:%M').time()
                    current_time = check_time.time()
                    
                    # Calcular diferença
                    diff_minutes = self._time_difference_minutes(end_time, current_time)
                    
                    if diff_minutes < -threshold:  # Saiu muito tarde
                        return {
                            'type': 'late_departure',
                            'severity': 'high',
                            'description': f'Permanência {abs(diff_minutes):.0f} minutos após horário',
                            'expected_time': expected_end,
                            'actual_time': current_time.strftime('%H:%M'),
                            'grade': grade
                        }
            
        except Exception as e:
            print(f"Erro ao verificar saída tarde: {e}")
        
        return None
    
    def _check_weekend_work(self, check_time: datetime, 
                          schedule_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verifica trabalho em fim de semana não programado
        """
        try:
            weekday = check_time.weekday()
            
            if weekday in [5, 6]:  # Sábado ou domingo
                has_weekend_schedule = False
                
                for grade, info in schedule_info.items():
                    schedule = info['parsed_schedule']
                    
                    if weekday == 5 and schedule.get('saturday'):
                        has_weekend_schedule = True
                    elif weekday == 6 and schedule.get('sunday'):
                        has_weekend_schedule = True
                
                if not has_weekend_schedule:
                    day_name = 'sábado' if weekday == 5 else 'domingo'
                    return {
                        'type': 'weekend_work',
                        'severity': 'high',
                        'description': f'Trabalho em {day_name} não programado',
                        'day': day_name,
                        'time': check_time.strftime('%H:%M')
                    }
            
        except Exception as e:
            print(f"Erro ao verificar trabalho fim de semana: {e}")
        
        return None
    
    def _check_holiday_work(self, check_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Verifica trabalho em feriado
        """
        try:
            # Lista de feriados nacionais (simplificada)
            holidays_2024 = [
                '01/01', '04/21', '05/01', '09/07', '10/12', '11/02', '11/15', '12/25'
            ]
            
            current_date = check_time.strftime('%m/%d')
            
            if current_date in holidays_2024:
                return {
                    'type': 'holiday_work',
                    'severity': 'high',
                    'description': 'Trabalho em feriado nacional',
                    'date': check_time.strftime('%d/%m/%Y'),
                    'time': check_time.strftime('%H:%M')
                }
            
        except Exception as e:
            print(f"Erro ao verificar feriado: {e}")
        
        return None
    
    def _check_lunch_time_anomaly(self, check_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Verifica horário de almoço atípico
        """
        try:
            current_time = check_time.time()
            
            # Horários típicos de almoço: 11:30 - 14:30
            typical_lunch_start = time(11, 30)
            typical_lunch_end = time(14, 30)
            
            # Se está no período típico de almoço
            if typical_lunch_start <= current_time <= typical_lunch_end:
                # Horários mais atípicos: antes das 12:00 ou depois das 14:00
                if current_time < time(12, 0):
                    return {
                        'type': 'early_lunch',
                        'severity': 'low',
                        'description': 'Horário de almoço muito cedo',
                        'time': current_time.strftime('%H:%M')
                    }
                elif current_time > time(14, 0):
                    return {
                        'type': 'late_lunch',
                        'severity': 'low',
                        'description': 'Horário de almoço muito tarde',
                        'time': current_time.strftime('%H:%M')
                    }
            
        except Exception as e:
            print(f"Erro ao verificar horário de almoço: {e}")
        
        return None
    
    def _calculate_risk_level(self, results: Dict[str, Any]) -> str:
        """
        Calcula nível de risco baseado na análise
        """
        try:
            risk_score = 0
            
            # Violação de horário
            if results.get('compliance_status') == 'violation':
                risk_score += 3
            
            # Anomalias detectadas
            anomalies = results.get('anomalies', [])
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'low')
                if severity == 'high':
                    risk_score += 2
                elif severity == 'medium':
                    risk_score += 1
            
            # Desvio de tempo
            deviation = results.get('deviation_minutes', 0)
            if deviation > 120:  # Mais de 2 horas
                risk_score += 2
            elif deviation > 60:  # Mais de 1 hora
                risk_score += 1
            
            # Determinar nível final
            if risk_score >= 5:
                return 'critical'
            elif risk_score >= 3:
                return 'high'
            elif risk_score >= 1:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            print(f"Erro ao calcular risco: {e}")
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