"""
Sistema integrado de análise usando todos os analyzers modulares
Orquestra face_analyzer, attribute_analyzer, badge_analyzer, schedule_analyzer e pattern_analyzer
"""

import torch
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import os

from analyzers import (
    FaceAnalyzer, 
    AttributeAnalyzer, 
    BadgeAnalyzer, 
    ScheduleAnalyzer, 
    PatternAnalyzer
)
from utils import load_config, save_results


class IntegratedAnalysisSystem:
    """
    Sistema principal que integra todos os analyzers especializados
    
    Funcionalidades:
    - Orquestra análise multi-modal (face, atributos, crachá, horários, padrões)
    - Correlaciona resultados entre analyzers
    - Gera análise de risco integrada
    - Produz relatórios consolidados
    - Detecta violações de conformidade
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = load_config(config_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() and 
                                  self.config['device']['use_cuda'] else 'cpu')
        
        # Inicializar analyzers
        self.analyzers = {}
        self._init_analyzers()
        
        # Histórico de análises para padrões
        self.analysis_history = []
        
        # Sistema de alertas
        self.alert_system = AlertSystem(self.config)
        
    def _init_analyzers(self):
        """
        Inicializa todos os analyzers especializados
        """
        try:
            print("Inicializando analyzers...")
            
            # Face Analyzer
            self.analyzers['face'] = FaceAnalyzer(self.config, self.device)
            face_model_path = self.config.get('models', {}).get('face_encodings')
            if face_model_path and os.path.exists(face_model_path):
                self.analyzers['face'].load_model(face_model_path)
            else:
                self.analyzers['face'].load_model()
            
            # Attribute Analyzer  
            self.analyzers['attributes'] = AttributeAnalyzer(self.config, self.device)
            attr_model_path = self.config.get('models', {}).get('attributes')
            self.analyzers['attributes'].load_model(attr_model_path)
            
            # Badge Analyzer
            self.analyzers['badge'] = BadgeAnalyzer(self.config, self.device)
            badge_model_path = self.config.get('models', {}).get('badge')
            self.analyzers['badge'].load_model(badge_model_path)
            
            # Schedule Analyzer
            self.analyzers['schedule'] = ScheduleAnalyzer(self.config)
            horarios_path = os.path.join('data', 'horarios.csv')
            rotinas_path = os.path.join('data', 'rotinas.json')
            self.analyzers['schedule'].load_data(horarios_path, rotinas_path)
            
            # Pattern Analyzer
            self.analyzers['patterns'] = PatternAnalyzer(self.config)
            
            print("✅ Todos os analyzers inicializados com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar analyzers: {e}")
    
    def analyze_comprehensive(self, image: torch.Tensor, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Realiza análise completa usando todos os analyzers
        """
        analysis_start = datetime.now()
        
        # Estrutura de resultado integrado
        integrated_results = {
            'timestamp': analysis_start.isoformat(),
            'metadata': metadata or {},
            'individual_analyses': {},
            'integrated_assessment': {},
            'compliance_check': {},
            'alerts': [],
            'recommendations': [],
            'confidence_scores': {},
            'execution_time': 0.0
        }
        
        try:
            # 1. ANÁLISES INDIVIDUAIS
            print("Executando análises individuais...")
            
            # Análise Facial
            face_results = self._run_face_analysis(image, metadata)
            integrated_results['individual_analyses']['face'] = face_results
            
            # Análise de Atributos  
            attr_results = self._run_attribute_analysis(image, metadata)
            integrated_results['individual_analyses']['attributes'] = attr_results
            
            # Análise de Crachá
            badge_results = self._run_badge_analysis(image, metadata)
            integrated_results['individual_analyses']['badge'] = badge_results
            
            # Análise de Horários
            schedule_results = self._run_schedule_analysis(metadata, face_results)
            integrated_results['individual_analyses']['schedule'] = schedule_results
            
            # 2. ANÁLISE INTEGRADA
            print("Realizando análise integrada...")
            
            # Correlacionar resultados
            correlation_results = self._correlate_analyses(integrated_results['individual_analyses'])
            integrated_results['integrated_assessment'] = correlation_results
            
            # Verificação de conformidade
            compliance_results = self._check_compliance(integrated_results['individual_analyses'])
            integrated_results['compliance_check'] = compliance_results
            
            # Sistema de alertas
            alerts = self._generate_alerts(integrated_results)
            integrated_results['alerts'] = alerts
            
            # Recomendações
            recommendations = self._generate_recommendations(integrated_results)
            integrated_results['recommendations'] = recommendations
            
            # Scores de confiança consolidados
            confidence_scores = self._calculate_confidence_scores(integrated_results['individual_analyses'])
            integrated_results['confidence_scores'] = confidence_scores
            
            # 3. ANÁLISE DE PADRÕES (se há dados históricos)
            if len(self.analysis_history) > 0:
                pattern_results = self._analyze_patterns_with_history(integrated_results)
                integrated_results['pattern_analysis'] = pattern_results
            
            # Adicionar à base de padrões
            self._add_to_pattern_analysis(integrated_results)
            
            # Tempo de execução
            execution_time = (datetime.now() - analysis_start).total_seconds()
            integrated_results['execution_time'] = execution_time
            
            print(f"✅ Análise completa executada em {execution_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Erro na análise integrada: {e}")
            integrated_results['error'] = str(e)
        
        return integrated_results
    
    def _run_face_analysis(self, image: torch.Tensor, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa análise facial
        """
        try:
            if 'face' not in self.analyzers:
                return {'error': 'Face analyzer não disponível'}
            
            results = self.analyzers['face'].analyze(image, metadata)
            
            # Enriquecer com informações de contexto
            if results.get('employee_detected', False):
                employee_info = results.get('employee_info', {})
                results['context'] = {
                    'known_employee': True,
                    'employee_name': employee_info.get('name', 'Unknown'),
                    'recognition_confidence': employee_info.get('confidence', 0.0)
                }
            else:
                results['context'] = {
                    'known_employee': False,
                    'security_concern': True,
                    'action_required': 'identify_person'
                }
            
            return results
            
        except Exception as e:
            return {'error': f'Erro na análise facial: {e}'}
    
    def _run_attribute_analysis(self, image: torch.Tensor, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa análise de atributos
        """
        try:
            if 'attributes' not in self.analyzers:
                return {'error': 'Attribute analyzer não disponível'}
            
            results = self.analyzers['attributes'].analyze(image, metadata)
            
            # Adicionar análise de conformidade corporativa
            corporate_analysis = self._analyze_corporate_dress_code(results)
            results['corporate_compliance'] = corporate_analysis
            
            return results
            
        except Exception as e:
            return {'error': f'Erro na análise de atributos: {e}'}
    
    def _run_badge_analysis(self, image: torch.Tensor, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa análise de crachá
        """
        try:
            if 'badge' not in self.analyzers:
                return {'error': 'Badge analyzer não disponível'}
            
            results = self.analyzers['badge'].analyze(image, metadata)
            
            # Adicionar verificação de política de crachás
            policy_check = self._check_badge_policy(results)
            results['policy_compliance'] = policy_check
            
            return results
            
        except Exception as e:
            return {'error': f'Erro na análise de crachá: {e}'}
    
    def _run_schedule_analysis(self, metadata: Dict[str, Any], face_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa análise de horários
        """
        try:
            if 'schedule' not in self.analyzers:
                return {'error': 'Schedule analyzer não disponível'}
            
            # Obter informações do funcionário se disponível
            employee_info = None
            if face_results.get('employee_detected', False):
                employee_info = face_results.get('employee_info', {})
            
            # Usar timestamp atual se não fornecido
            detection_time = datetime.now()
            if metadata and 'timestamp' in metadata:
                detection_time = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
            
            # Obter localização se disponível
            location = metadata.get('location', 'unknown')
            
            results = self.analyzers['schedule'].analyze_schedule_compliance(
                detection_time, employee_info, location
            )
            
            return results
            
        except Exception as e:
            return {'error': f'Erro na análise de horários: {e}'}
    
    def _correlate_analyses(self, individual_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Correlaciona resultados de diferentes analyzers
        """
        correlation = {
            'identity_consistency': self._check_identity_consistency(individual_analyses),
            'behavioral_consistency': self._check_behavioral_consistency(individual_analyses),
            'policy_violations': self._identify_policy_violations(individual_analyses),
            'risk_indicators': self._identify_risk_indicators(individual_analyses),
            'overall_assessment': {}
        }
        
        # Avaliação geral
        correlation['overall_assessment'] = self._calculate_overall_assessment(correlation)
        
        return correlation
    
    def _check_identity_consistency(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica consistência de identidade entre face e crachá
        """
        consistency = {
            'face_badge_match': False,
            'confidence_level': 0.0,
            'discrepancies': [],
            'verification_status': 'unknown'
        }
        
        try:
            face_data = analyses.get('face', {})
            badge_data = analyses.get('badge', {})
            
            # Verificar se há funcionário identificado pela face
            face_employee = face_data.get('employee_info', {}).get('name', '')
            
            # Verificar se há nome extraído do crachá
            badge_text = badge_data.get('extracted_text', [])
            badge_name = badge_data.get('potential_name', '')
            
            if face_employee and badge_name:
                # Comparar nomes (análise simples)
                name_similarity = self._calculate_name_similarity(face_employee, badge_name)
                
                if name_similarity > 0.8:
                    consistency['face_badge_match'] = True
                    consistency['confidence_level'] = name_similarity
                    consistency['verification_status'] = 'verified'
                else:
                    consistency['discrepancies'].append(
                        f"Nome na face ({face_employee}) não confere com crachá ({badge_name})"
                    )
                    consistency['verification_status'] = 'mismatch'
            
            elif face_employee and not badge_name:
                consistency['discrepancies'].append("Funcionário conhecido mas crachá não legível")
                consistency['verification_status'] = 'partial'
            
            elif not face_employee and badge_name:
                consistency['discrepancies'].append("Crachá legível mas funcionário não reconhecido")
                consistency['verification_status'] = 'partial'
            
            else:
                consistency['discrepancies'].append("Nem face nem crachá identificados")
                consistency['verification_status'] = 'unidentified'
                
        except Exception as e:
            consistency['error'] = str(e)
        
        return consistency
    
    def _check_behavioral_consistency(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica consistência comportamental
        """
        consistency = {
            'dress_code_schedule_match': True,
            'behavior_indicators': [],
            'anomaly_score': 0.0
        }
        
        try:
            attr_data = analyses.get('attributes', {})
            schedule_data = analyses.get('schedule', {})
            
            # Verificar se vestimenta é adequada para o horário
            formal_score = attr_data.get('formal_score', 0.0)
            expected_status = schedule_data.get('expected_status', 'unknown')
            
            if expected_status == 'should_be_present' and formal_score < 0.6:
                consistency['behavior_indicators'].append("Vestimenta informal em horário de trabalho")
                consistency['anomaly_score'] += 1.0
            
            # Verificar anomalias de horário
            anomalies = schedule_data.get('anomalies', [])
            consistency['anomaly_score'] += len(anomalies) * 0.5
            
        except Exception as e:
            consistency['error'] = str(e)
        
        return consistency
    
    def _identify_policy_violations(self, analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifica violações de política
        """
        violations = []
        
        try:
            # Violação: Sem crachá
            badge_data = analyses.get('badge', {})
            if not badge_data.get('has_valid_badge', False):
                violations.append({
                    'type': 'no_valid_badge',
                    'severity': 'high',
                    'description': 'Funcionário sem crachá válido',
                    'policy': 'Uso obrigatório de crachá'
                })
            
            # Violação: Fora do horário
            schedule_data = analyses.get('schedule', {})
            if schedule_data.get('compliance_status') == 'violation':
                violations.append({
                    'type': 'schedule_violation', 
                    'severity': 'medium',
                    'description': 'Presença fora do horário autorizado',
                    'policy': 'Controle de acesso por horário'
                })
            
            # Violação: Dress code
            attr_data = analyses.get('attributes', {})
            if not attr_data.get('dress_code_compliant', True):
                violations.append({
                    'type': 'dress_code_violation',
                    'severity': 'low',
                    'description': 'Não conformidade com dress code',
                    'policy': 'Código de vestimenta corporativo'
                })
            
            # Violação: Funcionário não identificado
            face_data = analyses.get('face', {})
            if not face_data.get('employee_detected', False) and face_data.get('detected', False):
                violations.append({
                    'type': 'unidentified_person',
                    'severity': 'high', 
                    'description': 'Pessoa não identificada no sistema',
                    'policy': 'Acesso restrito a funcionários autorizados'
                })
                
        except Exception as e:
            violations.append({
                'type': 'analysis_error',
                'severity': 'medium',
                'description': f'Erro na verificação de políticas: {e}',
                'policy': 'Sistema de monitoramento'
            })
        
        return violations
    
    def _identify_risk_indicators(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifica indicadores de risco
        """
        risk_indicators = {
            'security_risks': [],
            'operational_risks': [],
            'compliance_risks': [],
            'overall_risk_level': 'low'
        }
        
        try:
            # Riscos de segurança
            face_data = analyses.get('face', {})
            if not face_data.get('employee_detected', False) and face_data.get('detected', False):
                risk_indicators['security_risks'].append("Pessoa não autorizada detectada")
            
            # Riscos operacionais
            schedule_data = analyses.get('schedule', {})
            anomalies = schedule_data.get('anomalies', [])
            for anomaly in anomalies:
                if anomaly.get('severity') == 'high':
                    risk_indicators['operational_risks'].append(anomaly['description'])
            
            # Riscos de conformidade
            badge_data = analyses.get('badge', {})
            if badge_data.get('compliance_score', 0.0) < 0.7:
                risk_indicators['compliance_risks'].append("Baixa conformidade com política de crachás")
            
            # Calcular nível geral de risco
            total_risks = (len(risk_indicators['security_risks']) * 3 + 
                          len(risk_indicators['operational_risks']) * 2 + 
                          len(risk_indicators['compliance_risks']) * 1)
            
            if total_risks >= 6:
                risk_indicators['overall_risk_level'] = 'critical'
            elif total_risks >= 4:
                risk_indicators['overall_risk_level'] = 'high'
            elif total_risks >= 2:
                risk_indicators['overall_risk_level'] = 'medium'
            else:
                risk_indicators['overall_risk_level'] = 'low'
                
        except Exception as e:
            risk_indicators['error'] = str(e)
        
        return risk_indicators
    
    def _calculate_overall_assessment(self, correlation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula avaliação geral integrada
        """
        assessment = {
            'status': 'normal',
            'confidence': 0.0,
            'action_required': False,
            'priority': 'low',
            'summary': ''
        }
        
        try:
            # Avaliar baseado em violações e riscos
            violations = correlation.get('policy_violations', [])
            risk_level = correlation.get('risk_indicators', {}).get('overall_risk_level', 'low')
            
            high_severity_violations = [v for v in violations if v.get('severity') == 'high']
            
            if len(high_severity_violations) > 0 or risk_level in ['critical', 'high']:
                assessment['status'] = 'alert'
                assessment['action_required'] = True
                assessment['priority'] = 'high'
                assessment['summary'] = 'Situação requer atenção imediata'
                
            elif len(violations) > 0 or risk_level == 'medium':
                assessment['status'] = 'warning'
                assessment['action_required'] = True
                assessment['priority'] = 'medium'
                assessment['summary'] = 'Situação requer monitoramento'
                
            else:
                assessment['status'] = 'normal'
                assessment['action_required'] = False
                assessment['priority'] = 'low'
                assessment['summary'] = 'Situação dentro da normalidade'
            
            # Calcular confiança baseada na consistência
            identity_consistency = correlation.get('identity_consistency', {})
            behavioral_consistency = correlation.get('behavioral_consistency', {})
            
            confidence_factors = []
            
            if identity_consistency.get('verification_status') == 'verified':
                confidence_factors.append(0.4)
            elif identity_consistency.get('verification_status') == 'partial':
                confidence_factors.append(0.2)
            
            anomaly_score = behavioral_consistency.get('anomaly_score', 0.0)
            behavioral_confidence = max(0.0, 0.3 - (anomaly_score * 0.1))
            confidence_factors.append(behavioral_confidence)
            
            if len(violations) == 0:
                confidence_factors.append(0.3)
            
            assessment['confidence'] = sum(confidence_factors)
            
        except Exception as e:
            assessment['error'] = str(e)
        
        return assessment
    
    def _generate_alerts(self, integrated_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Gera alertas baseados na análise integrada
        """
        alerts = []
        
        try:
            violations = integrated_results.get('integrated_assessment', {}).get('policy_violations', [])
            risk_indicators = integrated_results.get('integrated_assessment', {}).get('risk_indicators', {})
            
            # Alertas de violação
            for violation in violations:
                if violation.get('severity') in ['high', 'critical']:
                    alerts.append({
                        'type': 'policy_violation',
                        'severity': violation['severity'],
                        'title': f"Violação: {violation['description']}",
                        'description': f"Política: {violation.get('policy', 'N/A')}",
                        'timestamp': datetime.now().isoformat(),
                        'requires_action': True
                    })
            
            # Alertas de risco de segurança
            security_risks = risk_indicators.get('security_risks', [])
            for risk in security_risks:
                alerts.append({
                    'type': 'security_risk',
                    'severity': 'high',
                    'title': 'Risco de Segurança',
                    'description': risk,
                    'timestamp': datetime.now().isoformat(),
                    'requires_action': True
                })
            
            # Alerta de pessoa não identificada
            face_analysis = integrated_results.get('individual_analyses', {}).get('face', {})
            if (face_analysis.get('detected', False) and 
                not face_analysis.get('employee_detected', False)):
                alerts.append({
                    'type': 'unidentified_person',
                    'severity': 'critical',
                    'title': 'Pessoa Não Identificada',
                    'description': 'Pessoa detectada mas não reconhecida no sistema',
                    'timestamp': datetime.now().isoformat(),
                    'requires_action': True
                })
                
        except Exception as e:
            alerts.append({
                'type': 'system_error',
                'severity': 'medium',
                'title': 'Erro no Sistema de Alertas',
                'description': str(e),
                'timestamp': datetime.now().isoformat(),
                'requires_action': False
            })
        
        return alerts
    
    def _generate_recommendations(self, integrated_results: Dict[str, Any]) -> List[str]:
        """
        Gera recomendações baseadas na análise
        """
        recommendations = []
        
        try:
            assessment = integrated_results.get('integrated_assessment', {}).get('overall_assessment', {})
            violations = integrated_results.get('integrated_assessment', {}).get('policy_violations', [])
            
            if assessment.get('action_required', False):
                if assessment.get('priority') == 'high':
                    recommendations.append("Ação imediata requerida - verificar situação no local")
                    recommendations.append("Notificar supervisor ou segurança")
                
                # Recomendações específicas por tipo de violação
                for violation in violations:
                    if violation['type'] == 'no_valid_badge':
                        recommendations.append("Solicitar apresentação de crachá válido")
                    elif violation['type'] == 'schedule_violation':
                        recommendations.append("Verificar autorização para presença fora do horário")
                    elif violation['type'] == 'unidentified_person':
                        recommendations.append("Identificar pessoa e verificar autorização de acesso")
                        recommendations.append("Considerar escolta até a saída se não autorizada")
            
            # Recomendações gerais
            badge_analysis = integrated_results.get('individual_analyses', {}).get('badge', {})
            if badge_analysis.get('compliance_score', 1.0) < 0.8:
                recommendations.append("Melhorar visibilidade do crachá")
            
            # Se não há recomendações específicas
            if not recommendations:
                recommendations.append("Continuar monitoramento de rotina")
                recommendations.append("Manter registros para análise de padrões")
                
        except Exception as e:
            recommendations.append(f"Erro ao gerar recomendações: {e}")
        
        return recommendations
    
    def _calculate_confidence_scores(self, individual_analyses: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcula scores de confiança consolidados
        """
        confidence_scores = {}
        
        try:
            for analyzer_name, results in individual_analyses.items():
                if 'confidence' in results:
                    confidence_scores[analyzer_name] = results['confidence']
                elif 'error' in results:
                    confidence_scores[analyzer_name] = 0.0
                else:
                    confidence_scores[analyzer_name] = 0.5
            
            # Score geral (média ponderada)
            if confidence_scores:
                weights = {'face': 0.3, 'badge': 0.25, 'attributes': 0.2, 'schedule': 0.25}
                weighted_sum = sum(confidence_scores.get(k, 0) * weights.get(k, 0.2) 
                                 for k in confidence_scores.keys())
                total_weight = sum(weights.get(k, 0.2) for k in confidence_scores.keys())
                confidence_scores['overall'] = weighted_sum / total_weight if total_weight > 0 else 0.0
            else:
                confidence_scores['overall'] = 0.0
                
        except Exception as e:
            confidence_scores['error'] = str(e)
        
        return confidence_scores
    
    def _analyze_patterns_with_history(self, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa padrões com base no histórico
        """
        try:
            # Preparar dados para análise de padrões
            detection_data = self._prepare_detection_data(current_results)
            
            # Adicionar à análise de padrões
            self.analyzers['patterns'].add_detection(detection_data)
            
            # Executar análise de padrões
            employee_id = self._extract_employee_id(current_results)
            pattern_results = self.analyzers['patterns'].analyze_patterns(employee_id, 24)
            
            return pattern_results
            
        except Exception as e:
            return {'error': f'Erro na análise de padrões: {e}'}
    
    def _prepare_detection_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara dados de detecção para análise de padrões
        """
        face_data = results.get('individual_analyses', {}).get('face', {})
        attr_data = results.get('individual_analyses', {}).get('attributes', {})
        badge_data = results.get('individual_analyses', {}).get('badge', {})
        
        return {
            'timestamp': results['timestamp'],
            'employee_id': self._extract_employee_id(results),
            'location': results.get('metadata', {}).get('location', 'unknown'),
            'confidence': results.get('confidence_scores', {}).get('overall', 0.0),
            'attributes': attr_data,
            'face_info': face_data,
            'badge_info': badge_data
        }
    
    def _extract_employee_id(self, results: Dict[str, Any]) -> str:
        """
        Extrai ID do funcionário dos resultados
        """
        face_data = results.get('individual_analyses', {}).get('face', {})
        
        if face_data.get('employee_detected', False):
            employee_info = face_data.get('employee_info', {})
            return employee_info.get('name', 'unknown')
        
        # Tentar extrair do crachá
        badge_data = results.get('individual_analyses', {}).get('badge', {})
        potential_id = badge_data.get('potential_id', '')
        if potential_id:
            return potential_id
        
        return 'unknown'
    
    def _add_to_pattern_analysis(self, results: Dict[str, Any]):
        """
        Adiciona resultados ao histórico para análise de padrões
        """
        try:
            # Limitar histórico em memória
            if len(self.analysis_history) >= 1000:
                self.analysis_history.pop(0)
            
            self.analysis_history.append({
                'timestamp': results['timestamp'],
                'employee_id': self._extract_employee_id(results),
                'assessment': results.get('integrated_assessment', {}),
                'violations': results.get('integrated_assessment', {}).get('policy_violations', []),
                'confidence_scores': results.get('confidence_scores', {})
            })
            
        except Exception as e:
            print(f"Erro ao adicionar ao histórico: {e}")
    
    # Métodos auxiliares
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calcula similaridade entre nomes (implementação simples)
        """
        try:
            # Normalizar nomes
            n1 = name1.lower().strip()
            n2 = name2.lower().strip()
            
            # Verificação exata
            if n1 == n2:
                return 1.0
            
            # Verificação de substring
            if n1 in n2 or n2 in n1:
                return 0.8
            
            # Verificação de palavras em comum
            words1 = set(n1.split())
            words2 = set(n2.split())
            
            if words1 & words2:  # Intersecção
                return 0.6
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _analyze_corporate_dress_code(self, attr_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análise específica de dress code corporativo
        """
        return {
            'compliant': attr_results.get('dress_code_compliant', False),
            'score': attr_results.get('formal_score', 0.0),
            'violations': attr_results.get('dress_code_violations', [])
        }
    
    def _check_badge_policy(self, badge_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verificação de política de crachás
        """
        return {
            'compliant': badge_results.get('has_valid_badge', False),
            'visible': badge_results.get('badge_visible', False),
            'readable': badge_results.get('employee_info_extracted', False)
        }
    
    def get_analysis_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera resumo legível da análise integrada
        """
        summary = {}
        
        # Status geral
        assessment = results.get('integrated_assessment', {}).get('overall_assessment', {})
        status = assessment.get('status', 'unknown')
        
        status_icons = {
            'normal': '✅',
            'warning': '⚠️',
            'alert': '🚨',
            'unknown': '❓'
        }
        
        summary['status'] = f"{status_icons.get(status, '❓')} Status: {status.title()}"
        summary['summary'] = assessment.get('summary', 'Sem informações')
        
        # Confiança geral
        confidence = results.get('confidence_scores', {}).get('overall', 0.0)
        summary['confidence'] = f"🎯 Confiança: {confidence:.1%}"
        
        # Alertas
        alerts = results.get('alerts', [])
        critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
        if critical_alerts:
            summary['alerts'] = f"🚨 {len(critical_alerts)} alerta(s) crítico(s)"
        elif alerts:
            summary['alerts'] = f"⚠️ {len(alerts)} alerta(s)"
        else:
            summary['alerts'] = "✅ Nenhum alerta"
        
        # Identificação
        face_data = results.get('individual_analyses', {}).get('face', {})
        if face_data.get('employee_detected', False):
            employee_name = face_data.get('employee_info', {}).get('name', 'Unknown')
            summary['identity'] = f"👤 {employee_name}"
        else:
            summary['identity'] = "❓ Não identificado"
        
        return summary


class AlertSystem:
    """
    Sistema de alertas e notificações
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_history = []
        
    def process_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Processa e registra alerta
        """
        try:
            # Adicionar timestamp se não existir
            if 'timestamp' not in alert:
                alert['timestamp'] = datetime.now().isoformat()
            
            # Adicionar ao histórico
            self.alert_history.append(alert)
            
            # Processar baseado na severidade
            if alert.get('severity') == 'critical':
                return self._handle_critical_alert(alert)
            elif alert.get('severity') == 'high':
                return self._handle_high_alert(alert)
            else:
                return self._handle_normal_alert(alert)
                
        except Exception as e:
            print(f"Erro ao processar alerta: {e}")
            return False
    
    def _handle_critical_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Processa alertas críticos
        """
        # Implementar notificação imediata
        print(f"🚨 ALERTA CRÍTICO: {alert['title']}")
        print(f"   Descrição: {alert['description']}")
        print(f"   Timestamp: {alert['timestamp']}")
        return True
    
    def _handle_high_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Processa alertas de alta prioridade
        """
        print(f"⚠️ ALERTA ALTO: {alert['title']}")
        print(f"   Descrição: {alert['description']}")
        return True
    
    def _handle_normal_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Processa alertas normais
        """
        print(f"ℹ️ ALERTA: {alert['title']}")
        return True 