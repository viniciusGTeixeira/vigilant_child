"""
Analyzer para análise de padrões comportamentais e detecção de mudanças
Monitora trajetos, horários de almoço, acessos a áreas e comportamentos incomuns
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
from collections import defaultdict, deque
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import Json
import os
import yaml

from .base_analyzer import BaseAnalyzer


@dataclass
class DetectionRecord:
    """Registro de uma detecção para análise de padrões"""
    timestamp: datetime
    employee_id: str
    location: str
    confidence: float
    attributes: Dict[str, Any]
    face_info: Dict[str, Any]
    badge_info: Dict[str, Any]


class PatternAnalyzer:
    """
    Analyzer especializado em análise de padrões comportamentais
    
    Funcionalidades:
    - Análise de trajetos e rotas usuais
    - Detecção de mudanças em horários de almoço
    - Monitoramento de acesso a áreas restritas
    - Identificação de comportamentos atípicos
    - Análise temporal de presença
    - Detecção de padrões sociais (agrupamentos)
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.detection_history = deque(maxlen=10000)  # Histórico limitado em memória
        self.employee_patterns = defaultdict(dict)
        self.location_patterns = defaultdict(dict)
        
        # Configurações específicas para padrões
        self.pattern_config = config.get('analyzers', {}).get('patterns', {
            'min_pattern_occurrences': 5,
            'pattern_window_days': 30,
            'lunch_time_variance_threshold': 30,  # minutos
            'route_deviation_threshold': 0.7,
            'restricted_areas': ['server_room', 'management', 'finance'],
            'social_distance_threshold': 2.0,  # metros
            'behavior_change_threshold': 0.3
        })
        
        # Inicializar conexão com banco de dados
        self._init_database()
    
    def _get_db_connection(self):
        """
        Cria uma nova conexão com o banco de dados PostgreSQL
        """
        db_config = self.config.get('database', {})
        return psycopg2.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            dbname=db_config.get('name', 'bigbrother'),
            user=db_config.get('user'),
            password=db_config.get('password')
        )
    
    def _init_database(self):
        """
        Inicializa banco de dados PostgreSQL para armazenar histórico de padrões
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Criar tabela de detecções
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS detections (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP NOT NULL,
                            employee_id VARCHAR(50),
                            location VARCHAR(100) NOT NULL,
                            confidence FLOAT,
                            attributes JSONB,
                            face_info JSONB,
                            badge_info JSONB
                        )
                    ''')
                    
                    # Criar tabela de padrões
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS patterns (
                            id SERIAL PRIMARY KEY,
                            employee_id VARCHAR(50) NOT NULL,
                            pattern_type VARCHAR(50) NOT NULL,
                            pattern_data JSONB NOT NULL,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            confidence FLOAT
                        )
                    ''')
                    
                    # Criar tabela de anomalias
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS anomalies (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP NOT NULL,
                            employee_id VARCHAR(50),
                            anomaly_type VARCHAR(50) NOT NULL,
                            description TEXT,
                            severity VARCHAR(20),
                            pattern_data JSONB
                        )
                    ''')
                    
                    # Criar índices para performance
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp)')
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_detections_employee ON detections(employee_id)')
                    cur.execute('CREATE INDEX IF NOT EXISTS idx_patterns_employee ON patterns(employee_id)')
                
                conn.commit()
            print("Banco de dados de padrões inicializado")
            
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {e}")
    
    def add_detection(self, detection_data: Dict[str, Any]) -> bool:
        """
        Adiciona nova detecção ao histórico para análise de padrões
        """
        try:
            # Criar registro de detecção
            record = DetectionRecord(
                timestamp=datetime.fromisoformat(detection_data['timestamp'].replace('Z', '+00:00')),
                employee_id=detection_data.get('employee_id', 'unknown'),
                location=detection_data.get('location', 'unknown'),
                confidence=detection_data.get('confidence', 0.0),
                attributes=detection_data.get('attributes', {}),
                face_info=detection_data.get('face_info', {}),
                badge_info=detection_data.get('badge_info', {})
            )
            
            # Adicionar ao histórico em memória
            self.detection_history.append(record)
            
            # Salvar no banco de dados
            self._save_detection_to_db(record)
            
            # Atualizar padrões do funcionário
            if record.employee_id != 'unknown':
                self._update_employee_patterns(record)
            
            # Atualizar padrões de localização
            self._update_location_patterns(record)
            
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar detecção: {e}")
            return False
    
    def analyze_patterns(self, employee_id: str = None, 
                        time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Analisa padrões comportamentais para um funcionário ou geral
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'employee_id': employee_id,
            'time_window_hours': time_window_hours,
            'patterns_detected': {},
            'anomalies': [],
            'behavioral_changes': [],
            'risk_assessment': {},
            'recommendations': []
        }
        
        try:
            # Obter dados relevantes
            recent_detections = self._get_recent_detections(employee_id, time_window_hours)
            historical_patterns = self._get_historical_patterns(employee_id)
            
            if len(recent_detections) == 0:
                results['status'] = 'no_data'
                return results
            
            # Análise de padrões temporais
            temporal_patterns = self._analyze_temporal_patterns(recent_detections)
            results['patterns_detected']['temporal'] = temporal_patterns
            
            # Análise de padrões espaciais (trajetos)
            spatial_patterns = self._analyze_spatial_patterns(recent_detections)
            results['patterns_detected']['spatial'] = spatial_patterns
            
            # Análise de mudanças comportamentais
            if historical_patterns:
                behavioral_changes = self._detect_behavioral_changes(
                    recent_detections, historical_patterns
                )
                results['behavioral_changes'] = behavioral_changes
            
            # Detecção de anomalias
            anomalies = self._detect_pattern_anomalies(recent_detections, employee_id)
            results['anomalies'] = anomalies
            
            # Análise de acesso a áreas restritas
            restricted_access = self._analyze_restricted_access(recent_detections)
            if restricted_access:
                results['anomalies'].extend(restricted_access)
            
            # Análise social (interações)
            social_patterns = self._analyze_social_patterns(recent_detections)
            results['patterns_detected']['social'] = social_patterns
            
            # Avaliação de risco
            risk_assessment = self._assess_behavioral_risk(results)
            results['risk_assessment'] = risk_assessment
            
            # Recomendações
            recommendations = self._generate_recommendations(results)
            results['recommendations'] = recommendations
            
        except Exception as e:
            print(f"Erro na análise de padrões: {e}")
            results['error'] = str(e)
        
        return results
    
    def _get_recent_detections(self, employee_id: str = None, 
                              hours: int = 24) -> List[DetectionRecord]:
        """
        Obtém detecções recentes do banco de dados
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    if employee_id:
                        cur.execute('''
                            SELECT timestamp, employee_id, location, confidence, 
                                   attributes, face_info, badge_info
                            FROM detections 
                            WHERE employee_id = %s AND timestamp > %s
                            ORDER BY timestamp DESC
                        ''', (employee_id, cutoff_time))
                    else:
                        cur.execute('''
                            SELECT timestamp, employee_id, location, confidence, 
                                   attributes, face_info, badge_info
                            FROM detections 
                            WHERE timestamp > %s
                            ORDER BY timestamp DESC
                        ''', (cutoff_time,))
                    
                    records = []
                    for row in cur.fetchall():
                        record = DetectionRecord(
                            timestamp=row[0],
                            employee_id=row[1] or 'unknown',
                            location=row[2],
                            confidence=row[3],
                            attributes=row[4],
                            face_info=row[5],
                            badge_info=row[6]
                        )
                        records.append(record)
                    
                    return records
                
        except Exception as e:
            print(f"Erro ao obter detecções recentes: {e}")
            return []
    
    def _get_historical_patterns(self, employee_id: str = None) -> Dict[str, Any]:
        """
        Obtém padrões históricos do funcionário
        """
        try:
            if not employee_id:
                return {}
            
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('''
                        SELECT pattern_type, pattern_data, confidence, updated_at
                        FROM patterns 
                        WHERE employee_id = %s
                        ORDER BY updated_at DESC
                    ''', (employee_id,))
                    
                    patterns = {}
                    for row in cur.fetchall():
                        pattern_type = row[0]
                        pattern_data = row[1]
                        patterns[pattern_type] = {
                            'data': pattern_data,
                            'confidence': row[2],
                            'updated_at': row[3]
                        }
                    
                    return patterns
                
        except Exception as e:
            print(f"Erro ao obter padrões históricos: {e}")
            return {}
    
    def _analyze_temporal_patterns(self, detections: List[DetectionRecord]) -> Dict[str, Any]:
        """
        Analisa padrões temporais nas detecções
        """
        patterns = {
            'arrival_times': [],
            'departure_times': [],
            'lunch_times': [],
            'peak_activity_hours': [],
            'presence_duration': {},
            'daily_patterns': {}
        }
        
        try:
            if not detections:
                return patterns
            
            # Agrupar detecções por dia
            daily_detections = defaultdict(list)
            for detection in detections:
                day_key = detection.timestamp.date().isoformat()
                daily_detections[day_key].append(detection)
            
            # Analisar cada dia
            for day, day_detections in daily_detections.items():
                day_detections.sort(key=lambda x: x.timestamp)
                
                # Primeiro e último detection do dia
                if len(day_detections) >= 2:
                    arrival_time = day_detections[0].timestamp.time()
                    departure_time = day_detections[-1].timestamp.time()
                    
                    patterns['arrival_times'].append(arrival_time.strftime('%H:%M'))
                    patterns['departure_times'].append(departure_time.strftime('%H:%M'))
                    
                    # Duração de presença
                    duration = (day_detections[-1].timestamp - day_detections[0].timestamp).total_seconds() / 3600
                    patterns['presence_duration'][day] = duration
                
                # Detectar horário de almoço (gap maior entre detecções)
                lunch_gap = self._detect_lunch_break(day_detections)
                if lunch_gap:
                    patterns['lunch_times'].append(lunch_gap)
                
                # Padrão de atividade ao longo do dia
                hourly_activity = self._calculate_hourly_activity(day_detections)
                patterns['daily_patterns'][day] = hourly_activity
            
            # Identificar horários de pico
            if patterns['daily_patterns']:
                peak_hours = self._identify_peak_hours(patterns['daily_patterns'])
                patterns['peak_activity_hours'] = peak_hours
            
        except Exception as e:
            print(f"Erro na análise temporal: {e}")
        
        return patterns
    
    def _detect_lunch_break(self, day_detections: List[DetectionRecord]) -> Optional[Dict[str, str]]:
        """
        Detecta horário de almoço baseado no maior gap entre detecções
        """
        try:
            if len(day_detections) < 2:
                return None
            
            max_gap = timedelta(0)
            lunch_start = None
            lunch_end = None
            
            for i in range(len(day_detections) - 1):
                gap = day_detections[i + 1].timestamp - day_detections[i].timestamp
                
                # Consideramos almoço se gap > 30 minutos e < 3 horas
                if timedelta(minutes=30) < gap < timedelta(hours=3):
                    if gap > max_gap:
                        max_gap = gap
                        lunch_start = day_detections[i].timestamp
                        lunch_end = day_detections[i + 1].timestamp
            
            if lunch_start and lunch_end:
                return {
                    'start_time': lunch_start.strftime('%H:%M'),
                    'end_time': lunch_end.strftime('%H:%M'),
                    'duration_minutes': int(max_gap.total_seconds() / 60)
                }
            
        except Exception as e:
            print(f"Erro ao detectar almoço: {e}")
        
        return None
    
    def _calculate_hourly_activity(self, day_detections: List[DetectionRecord]) -> Dict[int, int]:
        """
        Calcula atividade por hora do dia
        """
        hourly_count = defaultdict(int)
        
        for detection in day_detections:
            hour = detection.timestamp.hour
            hourly_count[hour] += 1
        
        return dict(hourly_count)
    
    def _identify_peak_hours(self, daily_patterns: Dict[str, Dict[int, int]]) -> List[int]:
        """
        Identifica horários de pico de atividade
        """
        try:
            # Agregar atividade por hora ao longo dos dias
            total_hourly = defaultdict(int)
            
            for day_pattern in daily_patterns.values():
                for hour, count in day_pattern.items():
                    total_hourly[hour] += count
            
            if not total_hourly:
                return []
            
            # Identificar horários com atividade acima da média
            avg_activity = sum(total_hourly.values()) / len(total_hourly)
            peak_hours = [hour for hour, count in total_hourly.items() 
                         if count > avg_activity * 1.5]
            
            return sorted(peak_hours)
            
        except Exception as e:
            print(f"Erro ao identificar picos: {e}")
            return []
    
    def _analyze_spatial_patterns(self, detections: List[DetectionRecord]) -> Dict[str, Any]:
        """
        Analisa padrões espaciais (trajetos e localizações)
        """
        patterns = {
            'frequent_locations': {},
            'location_transitions': {},
            'typical_routes': [],
            'time_spent_per_location': {},
            'area_preferences': {}
        }
        
        try:
            if not detections:
                return patterns
            
            # Contar frequência de localizações
            location_counts = defaultdict(int)
            for detection in detections:
                location_counts[detection.location] += 1
            
            patterns['frequent_locations'] = dict(location_counts)
            
            # Analisar transições entre localizações
            transitions = defaultdict(int)
            for i in range(len(detections) - 1):
                from_loc = detections[i].location
                to_loc = detections[i + 1].location
                
                if from_loc != to_loc:  # Só contar mudanças reais
                    transition_key = f"{from_loc} -> {to_loc}"
                    transitions[transition_key] += 1
            
            patterns['location_transitions'] = dict(transitions)
            
            # Calcular tempo gasto por localização
            time_per_location = self._calculate_time_per_location(detections)
            patterns['time_spent_per_location'] = time_per_location
            
            # Identificar rotas típicas
            typical_routes = self._identify_typical_routes(detections)
            patterns['typical_routes'] = typical_routes
            
        except Exception as e:
            print(f"Erro na análise espacial: {e}")
        
        return patterns
    
    def _calculate_time_per_location(self, detections: List[DetectionRecord]) -> Dict[str, float]:
        """
        Calcula tempo médio gasto em cada localização
        """
        location_times = defaultdict(list)
        
        try:
            current_location = None
            start_time = None
            
            for detection in sorted(detections, key=lambda x: x.timestamp):
                if current_location != detection.location:
                    # Mudou de localização
                    if current_location and start_time:
                        duration = (detection.timestamp - start_time).total_seconds() / 60  # minutos
                        location_times[current_location].append(duration)
                    
                    current_location = detection.location
                    start_time = detection.timestamp
            
            # Calcular médias
            avg_times = {}
            for location, times in location_times.items():
                if times:
                    avg_times[location] = sum(times) / len(times)
            
            return avg_times
            
        except Exception as e:
            print(f"Erro ao calcular tempo por localização: {e}")
            return {}
    
    def _identify_typical_routes(self, detections: List[DetectionRecord]) -> List[Dict[str, Any]]:
        """
        Identifica rotas típicas do funcionário
        """
        routes = []
        
        try:
            # Agrupar detecções consecutivas em sequências
            sequences = []
            current_sequence = []
            
            for detection in sorted(detections, key=lambda x: x.timestamp):
                if (not current_sequence or 
                    (detection.timestamp - current_sequence[-1].timestamp).total_seconds() < 3600):
                    # Mesma sequência (menos de 1 hora de gap)
                    current_sequence.append(detection)
                else:
                    # Nova sequência
                    if len(current_sequence) >= 3:  # Mínimo 3 localizações
                        sequences.append(current_sequence)
                    current_sequence = [detection]
            
            # Adicionar última sequência
            if len(current_sequence) >= 3:
                sequences.append(current_sequence)
            
            # Extrair padrões de rota
            route_patterns = defaultdict(int)
            
            for sequence in sequences:
                # Criar string da rota
                route_locations = [det.location for det in sequence]
                route_string = " -> ".join(route_locations)
                route_patterns[route_string] += 1
            
            # Converter para lista de rotas ordenadas por frequência
            for route, frequency in sorted(route_patterns.items(), 
                                         key=lambda x: x[1], reverse=True):
                if frequency >= 2:  # Pelo menos 2 ocorrências
                    routes.append({
                        'route': route,
                        'frequency': frequency,
                        'locations': route.split(' -> ')
                    })
            
        except Exception as e:
            print(f"Erro ao identificar rotas: {e}")
        
        return routes[:10]  # Top 10 rotas
    
    def _detect_behavioral_changes(self, recent_detections: List[DetectionRecord],
                                 historical_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detecta mudanças significativas no comportamento
        """
        changes = []
        
        try:
            # Analisar padrões recentes
            recent_temporal = self._analyze_temporal_patterns(recent_detections)
            recent_spatial = self._analyze_spatial_patterns(recent_detections)
            
            # Comparar com padrões históricos
            historical_temporal = historical_patterns.get('temporal', {}).get('data', {})
            historical_spatial = historical_patterns.get('spatial', {}).get('data', {})
            
            # Mudanças nos horários de chegada
            arrival_change = self._detect_time_pattern_change(
                recent_temporal.get('arrival_times', []),
                historical_temporal.get('arrival_times', []),
                'arrival_time'
            )
            if arrival_change:
                changes.append(arrival_change)
            
            # Mudanças nos horários de almoço
            lunch_change = self._detect_lunch_pattern_change(
                recent_temporal.get('lunch_times', []),
                historical_temporal.get('lunch_times', [])
            )
            if lunch_change:
                changes.append(lunch_change)
            
            # Mudanças nas localizações frequentes
            location_change = self._detect_location_pattern_change(
                recent_spatial.get('frequent_locations', {}),
                historical_spatial.get('frequent_locations', {})
            )
            if location_change:
                changes.append(location_change)
            
        except Exception as e:
            print(f"Erro ao detectar mudanças: {e}")
        
        return changes
    
    def _detect_time_pattern_change(self, recent_times: List[str], 
                                   historical_times: List[str],
                                   pattern_type: str) -> Optional[Dict[str, Any]]:
        """
        Detecta mudanças em padrões de horário
        """
        try:
            if not recent_times or not historical_times:
                return None
            
            # Converter para minutos para facilitar cálculos
            def time_to_minutes(time_str):
                h, m = map(int, time_str.split(':'))
                return h * 60 + m
            
            recent_minutes = [time_to_minutes(t) for t in recent_times]
            historical_minutes = [time_to_minutes(t) for t in historical_times]
            
            # Calcular médias
            recent_avg = np.mean(recent_minutes)
            historical_avg = np.mean(historical_minutes)
            
            # Diferença em minutos
            diff_minutes = abs(recent_avg - historical_avg)
            
            # Threshold para considerar mudança significativa
            threshold = self.pattern_config['lunch_time_variance_threshold']
            
            if diff_minutes > threshold:
                return {
                    'type': f'{pattern_type}_change',
                    'severity': 'medium' if diff_minutes < threshold * 2 else 'high',
                    'description': f'Mudança significativa no horário de {pattern_type}',
                    'recent_average': f"{int(recent_avg // 60):02d}:{int(recent_avg % 60):02d}",
                    'historical_average': f"{int(historical_avg // 60):02d}:{int(historical_avg % 60):02d}",
                    'difference_minutes': int(diff_minutes)
                }
            
        except Exception as e:
            print(f"Erro ao detectar mudança de horário: {e}")
        
        return None
    
    def _detect_lunch_pattern_change(self, recent_lunches: List[Dict[str, Any]], 
                                   historical_lunches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Detecta mudanças específicas nos padrões de almoço
        """
        try:
            if not recent_lunches or not historical_lunches:
                return None
            
            # Extrair horários de início
            recent_start_times = [lunch['start_time'] for lunch in recent_lunches]
            historical_start_times = [lunch['start_time'] for lunch in historical_lunches]
            
            # Usar função genérica para detectar mudança
            time_change = self._detect_time_pattern_change(
                recent_start_times, historical_start_times, 'lunch'
            )
            
            if time_change:
                # Adicionar informações específicas do almoço
                recent_durations = [lunch.get('duration_minutes', 0) for lunch in recent_lunches]
                historical_durations = [lunch.get('duration_minutes', 0) for lunch in historical_lunches]
                
                if recent_durations and historical_durations:
                    recent_avg_duration = np.mean(recent_durations)
                    historical_avg_duration = np.mean(historical_durations)
                    
                    time_change['recent_avg_duration'] = int(recent_avg_duration)
                    time_change['historical_avg_duration'] = int(historical_avg_duration)
                    time_change['duration_change'] = int(abs(recent_avg_duration - historical_avg_duration))
            
            return time_change
            
        except Exception as e:
            print(f"Erro ao detectar mudança no almoço: {e}")
        
        return None
    
    def _detect_location_pattern_change(self, recent_locations: Dict[str, int],
                                      historical_locations: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """
        Detecta mudanças nos padrões de localização
        """
        try:
            if not recent_locations or not historical_locations:
                return None
            
            # Normalizar contagens para percentuais
            recent_total = sum(recent_locations.values())
            historical_total = sum(historical_locations.values())
            
            recent_pct = {loc: count/recent_total for loc, count in recent_locations.items()}
            historical_pct = {loc: count/historical_total for loc, count in historical_locations.items()}
            
            # Calcular diferenças significativas
            significant_changes = []
            all_locations = set(recent_pct.keys()) | set(historical_pct.keys())
            
            for location in all_locations:
                recent_p = recent_pct.get(location, 0)
                historical_p = historical_pct.get(location, 0)
                
                diff = abs(recent_p - historical_p)
                
                if diff > 0.2:  # Mudança > 20%
                    change_type = 'increase' if recent_p > historical_p else 'decrease'
                    significant_changes.append({
                        'location': location,
                        'change_type': change_type,
                        'difference_pct': diff * 100,
                        'recent_pct': recent_p * 100,
                        'historical_pct': historical_p * 100
                    })
            
            if significant_changes:
                return {
                    'type': 'location_pattern_change',
                    'severity': 'medium',
                    'description': 'Mudança significativa nos locais frequentados',
                    'changes': significant_changes
                }
            
        except Exception as e:
            print(f"Erro ao detectar mudança de localização: {e}")
        
        return None
    
    def _detect_pattern_anomalies(self, detections: List[DetectionRecord],
                                 employee_id: str = None) -> List[Dict[str, Any]]:
        """
        Detecta anomalias nos padrões comportamentais
        """
        anomalies = []
        
        try:
            # Anomalia: Presença em horários muito incomuns
            unusual_hours = self._detect_unusual_hours(detections)
            anomalies.extend(unusual_hours)
            
            # Anomalia: Tempo excessivo em uma localização
            excessive_time = self._detect_excessive_location_time(detections)
            anomalies.extend(excessive_time)
            
            # Anomalia: Sequência de localizações incomum
            unusual_sequence = self._detect_unusual_location_sequence(detections)
            anomalies.extend(unusual_sequence)
            
            # Anomalia: Frequência de detecção muito baixa/alta
            frequency_anomaly = self._detect_frequency_anomaly(detections)
            if frequency_anomaly:
                anomalies.append(frequency_anomaly)
                
        except Exception as e:
            print(f"Erro ao detectar anomalias: {e}")
        
        return anomalies
    
    def _detect_unusual_hours(self, detections: List[DetectionRecord]) -> List[Dict[str, Any]]:
        """
        Detecta presença em horários incomuns
        """
        anomalies = []
        
        try:
            for detection in detections:
                hour = detection.timestamp.hour
                
                # Horários considerados incomuns: antes das 6h ou depois das 22h
                if hour < 6 or hour > 22:
                    anomalies.append({
                        'type': 'unusual_hour_presence',
                        'severity': 'medium' if 22 < hour < 24 or 5 < hour < 6 else 'high',
                        'description': f'Presença em horário incomum: {hour:02d}h',
                        'timestamp': detection.timestamp.isoformat(),
                        'location': detection.location,
                        'hour': hour
                    })
            
        except Exception as e:
            print(f"Erro ao detectar horários incomuns: {e}")
        
        return anomalies
    
    def _detect_excessive_location_time(self, detections: List[DetectionRecord]) -> List[Dict[str, Any]]:
        """
        Detecta tempo excessivo em uma localização
        """
        anomalies = []
        
        try:
            # Calcular tempo por localização
            time_per_location = self._calculate_time_per_location(detections)
            
            # Threshold: mais de 4 horas consecutivas em um local
            threshold_hours = 4
            
            for location, avg_time_minutes in time_per_location.items():
                if avg_time_minutes > threshold_hours * 60:
                    anomalies.append({
                        'type': 'excessive_location_time',
                        'severity': 'medium',
                        'description': f'Tempo excessivo em {location}: {avg_time_minutes:.0f} minutos',
                        'location': location,
                        'duration_minutes': avg_time_minutes,
                        'threshold_hours': threshold_hours
                    })
            
        except Exception as e:
            print(f"Erro ao detectar tempo excessivo: {e}")
        
        return anomalies
    
    def _detect_unusual_location_sequence(self, detections: List[DetectionRecord]) -> List[Dict[str, Any]]:
        """
        Detecta sequências de localização incomuns
        """
        anomalies = []
        
        try:
            # Verificar sequências de 3 localizações
            for i in range(len(detections) - 2):
                loc1 = detections[i].location
                loc2 = detections[i + 1].location
                loc3 = detections[i + 2].location
                
                sequence = f"{loc1} -> {loc2} -> {loc3}"
                
                # Verificar se é uma sequência que deveria ser flagrada
                # (implementar lógica específica baseada no layout do escritório)
                if self._is_unusual_sequence(loc1, loc2, loc3):
                    anomalies.append({
                        'type': 'unusual_location_sequence',
                        'severity': 'low',
                        'description': f'Sequência incomum de localizações: {sequence}',
                        'sequence': sequence,
                        'timestamp': detections[i].timestamp.isoformat()
                    })
            
        except Exception as e:
            print(f"Erro ao detectar sequência incomum: {e}")
        
        return anomalies
    
    def _is_unusual_sequence(self, loc1: str, loc2: str, loc3: str) -> bool:
        """
        Determina se uma sequência de localizações é incomum
        """
        # Exemplo: ir direto do escritório para área restrita sem passar pela recepção
        restricted_areas = self.pattern_config['restricted_areas']
        
        # Se foi para área restrita sem passar por checkpoint
        if (loc3 in restricted_areas and 
            loc1 not in restricted_areas and 
            'reception' not in loc2.lower() and 
            'entrance' not in loc2.lower()):
            return True
        
        return False
    
    def _detect_frequency_anomaly(self, detections: List[DetectionRecord]) -> Optional[Dict[str, Any]]:
        """
        Detecta anomalias na frequência de detecção
        """
        try:
            if len(detections) < 2:
                return None
            
            # Calcular intervalos entre detecções
            intervals = []
            for i in range(len(detections) - 1):
                interval = (detections[i + 1].timestamp - detections[i].timestamp).total_seconds() / 60
                intervals.append(interval)
            
            if not intervals:
                return None
            
            avg_interval = np.mean(intervals)
            max_interval = max(intervals)
            min_interval = min(intervals)
            
            # Anomalia: gaps muito grandes (> 3 horas) ou muito pequenos (< 1 minuto)
            if max_interval > 180:  # 3 horas
                return {
                    'type': 'large_detection_gap',
                    'severity': 'low',
                    'description': f'Gap grande entre detecções: {max_interval:.0f} minutos',
                    'max_interval_minutes': max_interval,
                    'average_interval_minutes': avg_interval
                }
            elif min_interval < 1:  # Menos de 1 minuto
                return {
                    'type': 'high_detection_frequency',
                    'severity': 'low',
                    'description': f'Detecções muito frequentes: {min_interval:.1f} minutos',
                    'min_interval_minutes': min_interval,
                    'average_interval_minutes': avg_interval
                }
            
        except Exception as e:
            print(f"Erro ao detectar anomalia de frequência: {e}")
        
        return None
    
    def _analyze_restricted_access(self, detections: List[DetectionRecord]) -> List[Dict[str, Any]]:
        """
        Analisa acessos a áreas restritas
        """
        access_anomalies = []
        
        try:
            restricted_areas = self.pattern_config['restricted_areas']
            
            for detection in detections:
                # Verificar se a localização contém áreas restritas
                for restricted_area in restricted_areas:
                    if restricted_area.lower() in detection.location.lower():
                        access_anomalies.append({
                            'type': 'restricted_area_access',
                            'severity': 'high',
                            'description': f'Acesso à área restrita: {detection.location}',
                            'location': detection.location,
                            'timestamp': detection.timestamp.isoformat(),
                            'restricted_area': restricted_area,
                            'confidence': detection.confidence
                        })
            
        except Exception as e:
            print(f"Erro ao analisar acesso restrito: {e}")
        
        return access_anomalies
    
    def _analyze_social_patterns(self, detections: List[DetectionRecord]) -> Dict[str, Any]:
        """
        Analisa padrões sociais e interações
        """
        social_patterns = {
            'concurrent_presences': [],
            'isolation_periods': [],
            'group_formations': [],
            'social_score': 0.0
        }
        
        try:
            # Simular análise de padrões sociais
            # (Em implementação real, seria necessário dados de múltiplos funcionários)
            
            # Detectar períodos de isolamento (sem outras detecções próximas)
            isolation_periods = self._detect_isolation_periods(detections)
            social_patterns['isolation_periods'] = isolation_periods
            
            # Calcular score social baseado na frequência de interações
            social_score = self._calculate_social_score(detections)
            social_patterns['social_score'] = social_score
            
        except Exception as e:
            print(f"Erro na análise social: {e}")
        
        return social_patterns
    
    def _detect_isolation_periods(self, detections: List[DetectionRecord]) -> List[Dict[str, Any]]:
        """
        Detecta períodos de isolamento prolongado
        """
        isolation_periods = []
        
        try:
            # Detectar gaps longos entre detecções como possível isolamento
            for i in range(len(detections) - 1):
                gap = (detections[i + 1].timestamp - detections[i].timestamp).total_seconds() / 60
                
                # Gap > 2 horas pode indicar isolamento
                if gap > 120:
                    isolation_periods.append({
                        'start_time': detections[i].timestamp.isoformat(),
                        'end_time': detections[i + 1].timestamp.isoformat(),
                        'duration_minutes': gap,
                        'severity': 'medium' if gap > 240 else 'low'  # 4 horas = high
                    })
            
        except Exception as e:
            print(f"Erro ao detectar isolamento: {e}")
        
        return isolation_periods
    
    def _calculate_social_score(self, detections: List[DetectionRecord]) -> float:
        """
        Calcula score de interação social (0-1)
        """
        try:
            if len(detections) == 0:
                return 0.0
            
            # Score baseado na frequência de detecções em áreas comuns
            common_areas = ['cafe', 'lunch', 'meeting', 'lounge', 'reception']
            
            common_area_detections = 0
            for detection in detections:
                for area in common_areas:
                    if area in detection.location.lower():
                        common_area_detections += 1
                        break
            
            # Normalizar pelo total de detecções
            social_score = common_area_detections / len(detections)
            
            return min(1.0, social_score)
            
        except Exception as e:
            print(f"Erro ao calcular score social: {e}")
            return 0.0
    
    def _assess_behavioral_risk(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia risco comportamental baseado na análise completa
        """
        risk_assessment = {
            'overall_risk_level': 'low',
            'risk_score': 0.0,
            'risk_factors': [],
            'protective_factors': []
        }
        
        try:
            risk_score = 0.0
            
            # Anomalias contribuem para o risco
            anomalies = analysis_results.get('anomalies', [])
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'low')
                if severity == 'high':
                    risk_score += 3
                elif severity == 'medium':
                    risk_score += 2
                else:
                    risk_score += 1
            
            # Mudanças comportamentais
            changes = analysis_results.get('behavioral_changes', [])
            risk_score += len(changes) * 1.5
            
            # Acesso a áreas restritas
            restricted_accesses = [a for a in anomalies if a.get('type') == 'restricted_area_access']
            risk_score += len(restricted_accesses) * 4
            
            # Normalizar score (0-10)
            risk_score = min(10.0, risk_score)
            
            # Determinar nível de risco
            if risk_score >= 7:
                risk_level = 'critical'
            elif risk_score >= 5:
                risk_level = 'high'
            elif risk_score >= 2:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            risk_assessment['overall_risk_level'] = risk_level
            risk_assessment['risk_score'] = risk_score
            
            # Identificar fatores específicos
            if anomalies:
                risk_assessment['risk_factors'].append(f"{len(anomalies)} anomalias detectadas")
            
            if changes:
                risk_assessment['risk_factors'].append(f"{len(changes)} mudanças comportamentais")
            
            if restricted_accesses:
                risk_assessment['risk_factors'].append(f"{len(restricted_accesses)} acessos a áreas restritas")
            
            # Fatores protetivos
            social_score = analysis_results.get('patterns_detected', {}).get('social', {}).get('social_score', 0)
            if social_score > 0.7:
                risk_assessment['protective_factors'].append("Alta interação social")
            
            patterns = analysis_results.get('patterns_detected', {})
            if patterns.get('temporal', {}).get('arrival_times'):
                risk_assessment['protective_factors'].append("Padrão de horários consistente")
            
        except Exception as e:
            print(f"Erro na avaliação de risco: {e}")
        
        return risk_assessment
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Gera recomendações baseadas na análise
        """
        recommendations = []
        
        try:
            risk_level = analysis_results.get('risk_assessment', {}).get('overall_risk_level', 'low')
            anomalies = analysis_results.get('anomalies', [])
            changes = analysis_results.get('behavioral_changes', [])
            
            # Recomendações baseadas no nível de risco
            if risk_level in ['high', 'critical']:
                recommendations.append("Aumentar frequência de monitoramento")
                recommendations.append("Revisar permissões de acesso")
                
            # Recomendações específicas por tipo de anomalia
            restricted_accesses = [a for a in anomalies if a.get('type') == 'restricted_area_access']
            if restricted_accesses:
                recommendations.append("Verificar autorização para áreas restritas")
                recommendations.append("Implementar autenticação adicional")
            
            unusual_hours = [a for a in anomalies if 'unusual_hour' in a.get('type', '')]
            if unusual_hours:
                recommendations.append("Investigar motivo da presença fora do horário")
                recommendations.append("Considerar ajustes no controle de acesso")
            
            # Recomendações para mudanças comportamentais
            if changes:
                recommendations.append("Verificar possíveis mudanças na função/projeto")
                recommendations.append("Considerar conversa com o funcionário")
            
            # Recomendações gerais
            if not recommendations:
                recommendations.append("Manter monitoramento de rotina")
                recommendations.append("Continuar análise de padrões")
            
        except Exception as e:
            print(f"Erro ao gerar recomendações: {e}")
        
        return recommendations
    
    def _save_detection_to_db(self, record: DetectionRecord):
        """
        Salva detecção no banco de dados
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('''
                        INSERT INTO detections 
                        (timestamp, employee_id, location, confidence, attributes, face_info, badge_info)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        record.timestamp,
                        record.employee_id,
                        record.location,
                        record.confidence,
                        Json(record.attributes),
                        Json(record.face_info),
                        Json(record.badge_info)
                    ))
                conn.commit()
        except Exception as e:
            print(f"Erro ao salvar detecção: {e}")
    
    def _update_employee_patterns(self, record: DetectionRecord):
        """
        Atualiza padrões do funcionário baseado em nova detecção
        """
        try:
            # Implementar lógica de atualização incremental de padrões
            # Por simplicidade, apenas atualizar contadores em memória
            employee_id = record.employee_id
            
            if employee_id not in self.employee_patterns:
                self.employee_patterns[employee_id] = {
                    'locations': defaultdict(int),
                    'hourly_activity': defaultdict(int),
                    'daily_patterns': defaultdict(list)
                }
            
            patterns = self.employee_patterns[employee_id]
            patterns['locations'][record.location] += 1
            patterns['hourly_activity'][record.timestamp.hour] += 1
            
        except Exception as e:
            print(f"Erro ao atualizar padrões do funcionário: {e}")
    
    def _update_location_patterns(self, record: DetectionRecord):
        """
        Atualiza padrões de localização
        """
        try:
            location = record.location
            
            if location not in self.location_patterns:
                self.location_patterns[location] = {
                    'hourly_usage': defaultdict(int),
                    'daily_usage': defaultdict(int),
                    'total_detections': 0
                }
            
            patterns = self.location_patterns[location]
            patterns['hourly_usage'][record.timestamp.hour] += 1
            patterns['daily_usage'][record.timestamp.weekday()] += 1
            patterns['total_detections'] += 1
            
        except Exception as e:
            print(f"Erro ao atualizar padrões de localização: {e}")
    
    def get_pattern_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera resumo legível da análise de padrões
        """
        summary = {}
        
        # Status geral
        risk_level = results.get('risk_assessment', {}).get('overall_risk_level', 'low')
        risk_icons = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
        summary['risk_status'] = f"{risk_icons.get(risk_level, '⚪')} Risco {risk_level}"
        
        # Anomalias
        anomalies = results.get('anomalies', [])
        if anomalies:
            high_severity = sum(1 for a in anomalies if a.get('severity') == 'high')
            if high_severity > 0:
                summary['anomalies'] = f'🚨 {high_severity} anomalia(s) crítica(s)'
            else:
                summary['anomalies'] = f'⚠️ {len(anomalies)} anomalia(s) detectada(s)'
        else:
            summary['anomalies'] = '✅ Nenhuma anomalia detectada'
        
        # Mudanças comportamentais
        changes = results.get('behavioral_changes', [])
        if changes:
            summary['behavior'] = f'📊 {len(changes)} mudança(s) comportamental(is)'
        else:
            summary['behavior'] = '✅ Comportamento consistente'
        
        # Padrões detectados
        patterns = results.get('patterns_detected', {})
        pattern_count = len([p for p in patterns.values() if p])
        summary['patterns'] = f'📈 {pattern_count} padrões identificados'
        
        return summary 