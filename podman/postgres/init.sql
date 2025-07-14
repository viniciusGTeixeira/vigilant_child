-- Tabela de Grades de Horário
CREATE TABLE schedule_grades (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(100),
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Horários dos Funcionários
CREATE TABLE employee_schedules (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER,
    grade_id INTEGER REFERENCES schedule_grades(id),
    schedule_text TEXT NOT NULL,
    messages TEXT,
    active BOOLEAN DEFAULT true,
    valid_from DATE,
    valid_until DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Rotinas de Trabalho
CREATE TABLE work_routines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Análises de Horário
CREATE TABLE schedule_analysis (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    employee_id INTEGER,
    location VARCHAR(100),
    compliance_status VARCHAR(50) NOT NULL,
    expected_status VARCHAR(50) NOT NULL,
    current_status VARCHAR(50) NOT NULL,
    schedule_match BOOLEAN NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    anomalies JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Verificações de Horário
CREATE TABLE schedule_checks (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    employee_id INTEGER,
    location VARCHAR(100),
    expected_status VARCHAR(50) NOT NULL,
    actual_status VARCHAR(50) NOT NULL,
    deviation_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Anomalias de Horário
CREATE TABLE schedule_anomalies (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    employee_id INTEGER,
    location VARCHAR(100),
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Feriados
CREATE TABLE holidays (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    location VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Associação Funcionário-Grade
CREATE TABLE employee_grades (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    grade_id INTEGER REFERENCES schedule_grades(id),
    active BOOLEAN DEFAULT true,
    valid_from DATE,
    valid_until DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimização
CREATE INDEX idx_employee_schedules_employee_id ON employee_schedules(employee_id);
CREATE INDEX idx_employee_schedules_grade_id ON employee_schedules(grade_id);
CREATE INDEX idx_schedule_analysis_employee_id ON schedule_analysis(employee_id);
CREATE INDEX idx_schedule_analysis_timestamp ON schedule_analysis(timestamp);
CREATE INDEX idx_schedule_checks_employee_id ON schedule_checks(employee_id);
CREATE INDEX idx_schedule_checks_timestamp ON schedule_checks(timestamp);
CREATE INDEX idx_schedule_anomalies_employee_id ON schedule_anomalies(employee_id);
CREATE INDEX idx_schedule_anomalies_timestamp ON schedule_anomalies(timestamp);
CREATE INDEX idx_holidays_date ON holidays(date);
CREATE INDEX idx_employee_grades_employee_id ON employee_grades(employee_id);
CREATE INDEX idx_employee_grades_grade_id ON employee_grades(grade_id);

-- Triggers para atualização automática de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_schedule_grades_updated_at
    BEFORE UPDATE ON schedule_grades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employee_schedules_updated_at
    BEFORE UPDATE ON employee_schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_work_routines_updated_at
    BEFORE UPDATE ON work_routines
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_holidays_updated_at
    BEFORE UPDATE ON holidays
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employee_grades_updated_at
    BEFORE UPDATE ON employee_grades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Dados iniciais para teste
INSERT INTO schedule_grades (name, description, location, priority)
VALUES 
    ('Padrão', 'Grade padrão de horário comercial', 'all', 0),
    ('Noturno', 'Grade para turno noturno', 'all', 1),
    ('Fim de Semana', 'Grade para trabalho aos fins de semana', 'all', 2);

INSERT INTO work_routines (name, description, priority, config)
VALUES (
    'Padrão Comercial',
    'Rotina padrão de trabalho comercial',
    0,
    '{"weekdays": {"start": "08:00", "end": "18:00", "lunch_start": "12:00", "lunch_end": "13:00"}, "saturday": {"start": "08:00", "end": "12:00"}, "sunday": {"closed": true}}'::jsonb
);

INSERT INTO holidays (date, name, type, description)
VALUES 
    ('2024-01-01', 'Ano Novo', 'nacional', 'Feriado de Ano Novo'),
    ('2024-04-21', 'Tiradentes', 'nacional', 'Dia de Tiradentes'),
    ('2024-05-01', 'Dia do Trabalho', 'nacional', 'Dia Internacional do Trabalho'),
    ('2024-09-07', 'Independência', 'nacional', 'Dia da Independência do Brasil'),
    ('2024-10-12', 'Nossa Senhora', 'nacional', 'Dia de Nossa Senhora Aparecida'),
    ('2024-11-02', 'Finados', 'nacional', 'Dia de Finados'),
    ('2024-11-15', 'República', 'nacional', 'Proclamação da República'),
    ('2024-12-25', 'Natal', 'nacional', 'Natal'); 