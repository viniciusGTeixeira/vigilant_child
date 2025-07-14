"""
Módulo para integração com MLflow
"""

import mlflow
import mlflow.pytorch
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from mlflow.models import infer_signature
from mlflow.exceptions import MlflowException

import torch
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Union
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report


class MLflowTracker:
    """
    Classe para integração com MLflow para tracking de experimentos
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mlflow_config = config.get('mlflow', {})
        
        # Configurar MLflow
        mlflow.set_tracking_uri(self.mlflow_config.get('tracking_uri', 'http://mlflow:5000'))
        
        # Cliente MLflow
        self.client = MlflowClient()
        
        # Configurações
        self.experiment_name = self.mlflow_config.get('experiment_name', 'bigbrother-cnn')
        self.auto_log = self.mlflow_config.get('auto_log', True)
        self.default_tags = self.mlflow_config.get('default_tags', {})
        
        # Configurar experimento
        self._setup_experiment()
        
        # Estado do run atual
        self.current_run = None
        self.current_run_id = None
    
    def _setup_experiment(self) -> None:
        """
        Configura o experimento MLflow
        """
        try:
            # Criar experimento se não existir
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    self.experiment_name,
                    artifact_location=self.mlflow_config.get('artifact_location')
                )
                print(f"Experimento criado: {self.experiment_name} (ID: {experiment_id})")
            else:
                experiment_id = experiment.experiment_id
                print(f"Usando experimento existente: {self.experiment_name} (ID: {experiment_id})")
            
            # Definir experimento ativo
            mlflow.set_experiment(self.experiment_name)
            
        except Exception as e:
            print(f"Erro ao configurar experimento: {e}")
            raise
    
    def start_run(self, run_name: Optional[str] = None, 
                  tags: Optional[Dict[str, str]] = None) -> str:
        """
        Inicia um novo run MLflow
        """
        try:
            # Combinar tags padrão com tags específicas
            all_tags = self.default_tags.copy()
            if tags:
                all_tags.update(tags)
            
            # Iniciar run
            self.current_run = mlflow.start_run(
                run_name=run_name,
                tags=all_tags
            )
            self.current_run_id = self.current_run.info.run_id
            
            # Configurar auto-logging se habilitado
            if self.auto_log:
                mlflow.pytorch.autolog()
                mlflow.sklearn.autolog()
            
            print(f"Run iniciado: {self.current_run_id}")
            return self.current_run_id
            
        except Exception as e:
            print(f"Erro ao iniciar run: {e}")
            raise
    
    def log_params(self, params: Dict[str, Any]) -> None:
        """
        Registra parâmetros no MLflow
        """
        try:
            if self.current_run is None:
                raise ValueError("Nenhum run ativo. Chame start_run() primeiro.")
            
            # Converter valores para tipos suportados
            clean_params = {}
            for key, value in params.items():
                if isinstance(value, (dict, list)):
                    clean_params[key] = json.dumps(value)
                else:
                    clean_params[key] = str(value)
            
            mlflow.log_params(clean_params)
            
        except Exception as e:
            print(f"Erro ao registrar parâmetros: {e}")
    
    def log_metrics(self, metrics: Dict[str, Union[float, int]], 
                   step: Optional[int] = None) -> None:
        """
        Registra métricas no MLflow
        """
        try:
            if self.current_run is None:
                raise ValueError("Nenhum run ativo. Chame start_run() primeiro.")
            
            # Filtrar apenas valores numéricos
            clean_metrics = {}
            for key, value in metrics.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    clean_metrics[key] = float(value)
            
            mlflow.log_metrics(clean_metrics, step=step)
            
        except Exception as e:
            print(f"Erro ao registrar métricas: {e}")
    
    def log_model(self, model: torch.nn.Module, 
                  model_name: str = "model",
                  signature: Optional[Any] = None,
                  input_example: Optional[Any] = None) -> None:
        """
        Registra modelo no MLflow
        """
        try:
            if self.current_run is None:
                raise ValueError("Nenhum run ativo. Chame start_run() primeiro.")
            
            # Registrar modelo PyTorch
            mlflow.pytorch.log_model(
                pytorch_model=model,
                artifact_path=model_name,
                signature=signature,
                input_example=input_example
            )
            
            print(f"Modelo registrado: {model_name}")
            
        except Exception as e:
            print(f"Erro ao registrar modelo: {e}")
    
    def log_artifact(self, local_path: str, 
                    artifact_path: Optional[str] = None) -> None:
        """
        Registra artifact no MLflow
        """
        try:
            if self.current_run is None:
                raise ValueError("Nenhum run ativo. Chame start_run() primeiro.")
            
            mlflow.log_artifact(local_path, artifact_path)
            
        except Exception as e:
            print(f"Erro ao registrar artifact: {e}")
    
    def log_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray,
                           class_names: Optional[List[str]] = None,
                           title: str = "Confusion Matrix") -> None:
        """
        Registra matriz de confusão como artifact
        """
        try:
            # Criar matriz de confusão
            cm = confusion_matrix(y_true, y_pred)
            
            # Criar figura
            plt.figure(figsize=(10, 8))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                       xticklabels=class_names, yticklabels=class_names)
            plt.title(title)
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
            
            # Salvar e registrar
            temp_path = f"/tmp/confusion_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(temp_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.log_artifact(temp_path, "plots")
            
            # Remover arquivo temporário
            os.remove(temp_path)
            
        except Exception as e:
            print(f"Erro ao registrar matriz de confusão: {e}")
    
    def log_classification_report(self, y_true: np.ndarray, y_pred: np.ndarray,
                                class_names: Optional[List[str]] = None) -> None:
        """
        Registra relatório de classificação
        """
        try:
            # Gerar relatório
            report = classification_report(
                y_true, y_pred, 
                target_names=class_names,
                output_dict=True
            )
            
            # Registrar métricas principais
            if 'accuracy' in report:
                self.log_metrics({'accuracy': report['accuracy']})
            
            if 'macro avg' in report:
                macro_avg = report['macro avg']
                self.log_metrics({
                    'macro_precision': macro_avg['precision'],
                    'macro_recall': macro_avg['recall'],
                    'macro_f1': macro_avg['f1-score']
                })
            
            if 'weighted avg' in report:
                weighted_avg = report['weighted avg']
                self.log_metrics({
                    'weighted_precision': weighted_avg['precision'],
                    'weighted_recall': weighted_avg['recall'],
                    'weighted_f1': weighted_avg['f1-score']
                })
            
            # Salvar relatório completo como artifact
            temp_path = f"/tmp/classification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(temp_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.log_artifact(temp_path, "reports")
            
            # Remover arquivo temporário
            os.remove(temp_path)
            
        except Exception as e:
            print(f"Erro ao registrar relatório de classificação: {e}")
    
    def log_training_plot(self, train_losses: List[float], 
                         val_losses: Optional[List[float]] = None,
                         train_accuracies: Optional[List[float]] = None,
                         val_accuracies: Optional[List[float]] = None) -> None:
        """
        Registra gráficos de treinamento
        """
        try:
            epochs = range(1, len(train_losses) + 1)
            
            # Criar subplots
            fig, axes = plt.subplots(1, 2, figsize=(15, 5))
            
            # Plot de loss
            axes[0].plot(epochs, train_losses, 'b-', label='Training Loss')
            if val_losses:
                axes[0].plot(epochs, val_losses, 'r-', label='Validation Loss')
            axes[0].set_title('Training and Validation Loss')
            axes[0].set_xlabel('Epochs')
            axes[0].set_ylabel('Loss')
            axes[0].legend()
            axes[0].grid(True)
            
            # Plot de accuracy
            if train_accuracies:
                axes[1].plot(epochs, train_accuracies, 'b-', label='Training Accuracy')
                if val_accuracies:
                    axes[1].plot(epochs, val_accuracies, 'r-', label='Validation Accuracy')
                axes[1].set_title('Training and Validation Accuracy')
                axes[1].set_xlabel('Epochs')
                axes[1].set_ylabel('Accuracy')
                axes[1].legend()
                axes[1].grid(True)
            else:
                axes[1].axis('off')
            
            plt.tight_layout()
            
            # Salvar e registrar
            temp_path = f"/tmp/training_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(temp_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.log_artifact(temp_path, "plots")
            
            # Remover arquivo temporário
            os.remove(temp_path)
            
        except Exception as e:
            print(f"Erro ao registrar gráfico de treinamento: {e}")
    
    def end_run(self, status: str = "FINISHED") -> None:
        """
        Finaliza o run atual
        """
        try:
            if self.current_run is None:
                print("Nenhum run ativo para finalizar.")
                return
            
            mlflow.end_run(status=status)
            print(f"Run finalizado: {self.current_run_id}")
            
            self.current_run = None
            self.current_run_id = None
            
        except Exception as e:
            print(f"Erro ao finalizar run: {e}")
    
    def register_model(self, model_name: str, 
                      model_version: Optional[str] = None,
                      stage: str = "Development") -> None:
        """
        Registra modelo no Model Registry
        """
        try:
            if self.current_run is None:
                raise ValueError("Nenhum run ativo. Chame start_run() primeiro.")
            
            # Registrar modelo
            model_uri = f"runs:/{self.current_run_id}/model"
            mv = mlflow.register_model(model_uri, model_name)
            
            # Transicionar para stage especificado
            if stage != "None":
                self.client.transition_model_version_stage(
                    name=model_name,
                    version=mv.version,
                    stage=stage
                )
            
            print(f"Modelo registrado: {model_name} v{mv.version} ({stage})")
            
        except Exception as e:
            print(f"Erro ao registrar modelo: {e}")
    
    def get_model(self, model_name: str, stage: str = "Production") -> Any:
        """
        Carrega modelo do Model Registry
        """
        try:
            model_uri = f"models:/{model_name}/{stage}"
            model = mlflow.pytorch.load_model(model_uri)
            return model
            
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            return None
    
    def search_runs(self, experiment_name: Optional[str] = None,
                   filter_string: Optional[str] = None,
                   max_results: int = 100) -> pd.DataFrame:
        """
        Busca runs no MLflow
        """
        try:
            exp_name = experiment_name or self.experiment_name
            experiment = mlflow.get_experiment_by_name(exp_name)
            
            if experiment is None:
                raise ValueError(f"Experimento não encontrado: {exp_name}")
            
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=filter_string,
                max_results=max_results
            )
            
            return runs
            
        except Exception as e:
            print(f"Erro ao buscar runs: {e}")
            return pd.DataFrame()
    
    def close(self) -> None:
        """
        Fecha conexões e finaliza run se ativo
        """
        try:
            if self.current_run is not None:
                self.end_run()
        except Exception as e:
            print(f"Erro ao fechar MLflow tracker: {e}") 