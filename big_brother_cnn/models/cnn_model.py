import torch
import torch.nn as nn
import torchvision.models as models
import yaml
import os

class BigBrotherCNN(nn.Module):
    def __init__(self, config_path='config.yaml'):
        super(BigBrotherCNN, self).__init__()
        
        # Carregar configurações
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.num_classes = self.config['model']['num_classes']
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Construir modelo
        self.model = self._build_model()
        self.model.to(self.device)
        
        # Configurar otimizador e loss
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), 
            lr=self.config['model']['learning_rate']
        )
        self.loss_fn = nn.CrossEntropyLoss()
        
    def _build_model(self):
        """
        Constrói a arquitetura CNN usando ResNet-18 pré-treinado
        """
        # Usar ResNet-18 pré-treinado como backbone
        backbone = models.resnet18(pretrained=True)
        
        # Remover a última camada de classificação
        self.backbone = nn.Sequential(*list(backbone.children())[:-1])
        
        # Congelar as camadas do backbone para transfer learning
        if self.config['model'].get('freeze_backbone', True):
            for param in self.backbone.parameters():
                param.requires_grad = False
        
        # Adicionar camadas de classificação personalizadas
        model = nn.Sequential(
            self.backbone,
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, self.num_classes)
        )
        
        return model
    
    def forward(self, x):
        """
        Forward pass do modelo
        """
        return self.model(x)
    
    def train_model(self, train_loader, val_loader):
        """
        Treina o modelo com os dados fornecidos
        """
        epochs = self.config['model']['epochs']
        best_val_loss = float('inf')
        patience = self.config['training']['early_stopping_patience']
        patience_counter = 0
        
        train_losses = []
        val_losses = []
        
        for epoch in range(epochs):
            # Fase de treinamento
            self.model.train()
            train_loss = 0.0
            
            for batch_idx, (data, target) in enumerate(train_loader):
                data, target = data.to(self.device), target.to(self.device)
                
                self.optimizer.zero_grad()
                output = self.model(data)
                loss = self.loss_fn(output, target)
                loss.backward()
                self.optimizer.step()
                
                train_loss += loss.item()
            
            # Fase de validação
            self.model.eval()
            val_loss = 0.0
            correct = 0
            total = 0
            
            with torch.no_grad():
                for data, target in val_loader:
                    data, target = data.to(self.device), target.to(self.device)
                    output = self.model(data)
                    val_loss += self.loss_fn(output, target).item()
                    
                    _, predicted = torch.max(output.data, 1)
                    total += target.size(0)
                    correct += (predicted == target).sum().item()
            
            # Calcular métricas médias
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            accuracy = 100 * correct / total
            
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            
            print(f'Epoch {epoch+1}/{epochs}: '
                  f'Train Loss: {train_loss:.4f}, '
                  f'Val Loss: {val_loss:.4f}, '
                  f'Val Acc: {accuracy:.2f}%')
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Salvar melhor modelo
                self.save_checkpoint(epoch, 'best_model.pth')
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f'Early stopping na época {epoch+1}')
                    break
        
        return train_losses, val_losses
    
    def predict(self, x):
        """
        Realiza predições em novos dados
        """
        self.model.eval()
        with torch.no_grad():
            if isinstance(x, torch.Tensor):
                x = x.to(self.device)
            else:
                x = torch.tensor(x, dtype=torch.float32).to(self.device)
                
            output = self.model(x)
            probabilities = torch.nn.functional.softmax(output, dim=1)
            return probabilities.cpu().numpy()
    
    def save_checkpoint(self, epoch, filename):
        """
        Salva checkpoint do modelo
        """
        checkpoint_dir = self.config['training']['checkpoint_dir']
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config
        }
        
        torch.save(checkpoint, os.path.join(checkpoint_dir, filename))
        print(f'Checkpoint salvo: {filename}')
    
    def load_checkpoint(self, filename):
        """
        Carrega checkpoint do modelo
        """
        checkpoint_path = os.path.join(self.config['training']['checkpoint_dir'], filename)
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        return checkpoint['epoch']
    
    def get_model_summary(self):
        """
        Retorna informações sobre o modelo
        """
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'device': str(self.device),
            'num_classes': self.num_classes
        } 