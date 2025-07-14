# Contratos de Interface

## 1. REST APIs

### 1.1 Autenticação
```json
POST /api/v1/auth/login
{
    "username": "string",
    "password": "string"
}

Response 200:
{
    "token": "string",
    "refresh_token": "string",
    "expires_in": "number"
}
```

### 1.2 Análise em Tempo Real
```json
POST /api/v1/analysis/realtime
{
    "frame": "base64_string",
    "camera_id": "string",
    "timestamp": "string",
    "config": {
        "face_detection": "boolean",
        "attribute_analysis": "boolean",
        "badge_detection": "boolean",
        "schedule_check": "boolean",
        "pattern_analysis": "boolean"
    }
}

Response 200:
{
    "analysis_id": "string",
    "results": {
        "face": {
            "detected": "boolean",
            "employee_id": "string",
            "confidence": "number"
        },
        "attributes": {
            "dress_code": "boolean",
            "safety_equipment": "boolean",
            "details": ["string"]
        },
        "badge": {
            "detected": "boolean",
            "valid": "boolean",
            "number": "string"
        },
        "schedule": {
            "compliant": "boolean",
            "details": "string"
        },
        "pattern": {
            "anomaly": "boolean",
            "score": "number"
        }
    },
    "alerts": [{
        "type": "string",
        "severity": "string",
        "message": "string"
    }]
}
```

### 1.3 Gestão de Funcionários
```json
POST /api/v1/employees
{
    "name": "string",
    "id": "string",
    "department": "string",
    "access_level": "string",
    "schedule": {
        "start": "string",
        "end": "string",
        "days": ["string"]
    },
    "face_data": "base64_string",
    "badge_number": "string"
}

GET /api/v1/employees/{id}
Response 200:
{
    "employee": {
        "name": "string",
        "id": "string",
        "department": "string",
        "access_level": "string",
        "schedule": {
            "start": "string",
            "end": "string",
            "days": ["string"]
        },
        "status": "string",
        "last_seen": "string"
    }
}
```

## 2. WebSocket APIs

### 2.1 Stream de Alertas
```json
// Connect to: ws://api/v1/alerts/stream

// Server -> Client
{
    "type": "ALERT",
    "data": {
        "id": "string",
        "timestamp": "string",
        "camera_id": "string",
        "alert_type": "string",
        "severity": "string",
        "details": {
            "employee_id": "string",
            "violation_type": "string",
            "location": "string"
        }
    }
}
```

### 2.2 Métricas em Tempo Real
```json
// Connect to: ws://api/v1/metrics/stream

// Server -> Client
{
    "type": "METRICS",
    "data": {
        "timestamp": "string",
        "system": {
            "cpu_usage": "number",
            "gpu_usage": "number",
            "memory_usage": "number"
        },
        "analysis": {
            "frames_processed": "number",
            "detection_rate": "number",
            "false_positives": "number"
        }
    }
}
```

## 3. gRPC Services

### 3.1 Análise de Vídeo
```protobuf
service VideoAnalysis {
    rpc AnalyzeStream (stream Frame) returns (stream AnalysisResult);
    rpc GetStatus (StatusRequest) returns (StatusResponse);
}

message Frame {
    string camera_id = 1;
    bytes data = 2;
    string timestamp = 3;
}

message AnalysisResult {
    string frame_id = 1;
    repeated Detection detections = 2;
    repeated Alert alerts = 3;
}
```

### 3.2 Gerenciamento de Modelos
```protobuf
service ModelManagement {
    rpc UpdateModel (ModelData) returns (UpdateStatus);
    rpc GetModelInfo (ModelRequest) returns (ModelInfo);
}

message ModelData {
    string model_type = 1;
    bytes model_file = 2;
    string version = 3;
}

message ModelInfo {
    string model_type = 1;
    string version = 2;
    string status = 3;
    map<string, float> metrics = 4;
}
```

## 4. Message Queue Topics

### 4.1 Eventos de Sistema
```json
// Topic: system.events
{
    "event_type": "string",
    "timestamp": "string",
    "source": "string",
    "data": {
        "type": "string",
        "details": "object"
    }
}
```

### 4.2 Processamento em Batch
```json
// Topic: analysis.batch
{
    "batch_id": "string",
    "frames": [{
        "frame_id": "string",
        "data": "base64_string",
        "metadata": {
            "camera_id": "string",
            "timestamp": "string"
        }
    }]
}
```

## 5. Database Schemas

### 5.1 Employees
```sql
CREATE TABLE employees (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    access_level VARCHAR(20),
    face_data BYTEA,
    badge_number VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Analysis Results
```sql
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    camera_id VARCHAR(50),
    employee_id VARCHAR(50),
    analysis_type VARCHAR(20),
    result JSONB,
    confidence FLOAT,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

## 6. Cache Keys

### 6.1 Padrão de Keys
```
# Employee Data
employee:{id}:info
employee:{id}:face
employee:{id}:schedule

# Analysis Results
analysis:{camera_id}:latest
analysis:{employee_id}:today
analysis:stats:{type}:{timeframe}

# System Status
system:status:{component}
system:metrics:{type}:current
```

## 7. Formatos de Arquivo

### 7.1 Configuração
```yaml
system:
  mode: "production"
  log_level: "info"
  
analyzers:
  face:
    model: "path/to/model"
    threshold: 0.95
    
  attribute:
    models:
      - name: "dress_code"
        path: "path/to/model"
      - name: "safety"
        path: "path/to/model"
        
  badge:
    ocr_engine: "tesseract"
    validation_rules: ["regex", "checksum"]
    
  schedule:
    tolerance: 15  # minutes
    
  pattern:
    window_size: 24  # hours
    anomaly_threshold: 0.8
```

### 7.2 Logs
```json
{
    "timestamp": "ISO8601",
    "level": "string",
    "service": "string",
    "trace_id": "string",
    "message": "string",
    "data": {
        "context": "object",
        "metrics": "object"
    }
}
```

## 8. Headers HTTP

### 8.1 Requisições
```
Authorization: Bearer {token}
Content-Type: application/json
X-Request-ID: {uuid}
X-Client-Version: {version}
X-Camera-ID: {camera_id}
```

### 8.2 Respostas
```
X-RateLimit-Limit: {number}
X-RateLimit-Remaining: {number}
X-Processing-Time: {ms}
X-Analysis-ID: {uuid}
```

## 9. Códigos de Erro

### 9.1 HTTP Status
```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": ["string"],
        "trace_id": "string"
    }
}
```

### 9.2 Códigos Internos
```json
{
    "ANALYSIS_ERROR": {
        "1001": "Face detection failed",
        "1002": "Invalid badge format",
        "1003": "Schedule validation error"
    },
    "SYSTEM_ERROR": {
        "2001": "GPU unavailable",
        "2002": "Model loading failed",
        "2003": "Database connection error"
    }
} 