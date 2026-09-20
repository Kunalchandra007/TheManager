-- TheManager PostgreSQL/Aurora schema. Safe to re-run on an existing schema.
CREATE TABLE IF NOT EXISTS dim_project (project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, project_code VARCHAR(20) UNIQUE NOT NULL, project_name VARCHAR(100) NOT NULL, project_country VARCHAR(100), project_location VARCHAR(255), created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS dim_work_package (work_package_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, work_package_code VARCHAR(20) UNIQUE NOT NULL, work_package_name VARCHAR(100) NOT NULL, wbs VARCHAR(50));
CREATE TABLE IF NOT EXISTS dim_equipment (equipment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, equipment_code VARCHAR(20) UNIQUE NOT NULL, equipment_name VARCHAR(100) NOT NULL, equipment_type VARCHAR(50), specifications TEXT);
CREATE TABLE IF NOT EXISTS dim_milestone (milestone_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, milestone_number VARCHAR(20), milestone_activity VARCHAR(100) NOT NULL, milestone_description VARCHAR(255), UNIQUE(milestone_activity, milestone_description));
CREATE TABLE IF NOT EXISTS dim_supplier (supplier_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, supplier_number VARCHAR(20) UNIQUE NOT NULL, supplier_name VARCHAR(100) NOT NULL, contact_name VARCHAR(100), contact_number VARCHAR(50), email_address VARCHAR(100));
CREATE TABLE IF NOT EXISTS dim_equipment_supplier (equipment_supplier_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, equipment_id BIGINT NOT NULL REFERENCES dim_equipment, supplier_id BIGINT NOT NULL REFERENCES dim_supplier, unit_cost NUMERIC(18,2) NOT NULL, is_preferred BOOLEAN NOT NULL DEFAULT false, lead_time_days INTEGER, remarks TEXT, UNIQUE(equipment_id, supplier_id));
CREATE TABLE IF NOT EXISTS fact_purchase_order (purchase_order_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, purchase_order_number VARCHAR(50) NOT NULL, line_item VARCHAR(20), project_id BIGINT NOT NULL REFERENCES dim_project, work_package_id BIGINT NOT NULL REFERENCES dim_work_package, supplier_id BIGINT NOT NULL REFERENCES dim_supplier, equipment_id BIGINT NOT NULL REFERENCES dim_equipment, short_text TEXT, remarks TEXT, amount NUMERIC(18,2), UNIQUE(purchase_order_number, line_item));
CREATE TABLE IF NOT EXISTS fact_p6_schedule (p6_schedule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, project_id BIGINT NOT NULL REFERENCES dim_project, work_package_id BIGINT NOT NULL REFERENCES dim_work_package, equipment_id BIGINT NOT NULL REFERENCES dim_equipment, milestone_id BIGINT NOT NULL REFERENCES dim_milestone, p6_schedule_due_date DATE NOT NULL, UNIQUE(project_id, work_package_id, equipment_id, milestone_id));
CREATE TABLE IF NOT EXISTS fact_equipment_milestone_schedule (equipment_milestone_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, equipment_id BIGINT NOT NULL REFERENCES dim_equipment, project_id BIGINT NOT NULL REFERENCES dim_project, work_package_id BIGINT NOT NULL REFERENCES dim_work_package, milestone_id BIGINT NOT NULL REFERENCES dim_milestone, purchase_order_id BIGINT REFERENCES fact_purchase_order, equipment_milestone_due_date DATE NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'Active', UNIQUE(project_id, work_package_id, equipment_id, milestone_id));
CREATE TABLE IF NOT EXISTS dim_manufacturing_location (manufacturing_location_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, equipment_id BIGINT NOT NULL REFERENCES dim_equipment, supplier_id BIGINT NOT NULL REFERENCES dim_supplier, location_address VARCHAR(255) NOT NULL, UNIQUE(equipment_id, supplier_id));
CREATE TABLE IF NOT EXISTS dim_logistics_info (logistics_info_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, equipment_id BIGINT NOT NULL REFERENCES dim_equipment, supplier_id BIGINT NOT NULL REFERENCES dim_supplier, logistics_method VARCHAR(50) NOT NULL, shipping_port VARCHAR(100), receiving_port VARCHAR(100), UNIQUE(equipment_id, supplier_id));
CREATE TABLE IF NOT EXISTS fact_risk_report (report_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, session_id VARCHAR(100) NOT NULL, conversation_id UUID NOT NULL, filename VARCHAR(255) NOT NULL, s3_key TEXT NOT NULL, report_type VARCHAR(50) NOT NULL DEFAULT 'comprehensive', created_at TIMESTAMPTZ NOT NULL DEFAULT now());

CREATE OR REPLACE VIEW v_schedule_comparison AS
SELECT p.project_id, p.project_name, p.project_code, p.project_country, p.project_location,
 eq.equipment_id, eq.equipment_code, eq.equipment_name, eq.equipment_type,
 wp.work_package_id, wp.work_package_code, wp.work_package_name, m.milestone_id, m.milestone_number, m.milestone_activity,
 ps.p6_schedule_due_date, ems.equipment_milestone_due_date,
 (ems.equipment_milestone_due_date - ps.p6_schedule_due_date) AS days_variance,
 (ps.p6_schedule_due_date - CURRENT_DATE) AS days_until_p6_due,
 s.supplier_id, s.supplier_name, s.supplier_number, po.purchase_order_id, po.purchase_order_number, po.line_item, po.amount,
 es.lead_time_days AS supplier_lead_time, ml.location_address AS manufacturing_location,
 li.shipping_port, li.receiving_port, li.logistics_method
FROM fact_p6_schedule ps
JOIN fact_equipment_milestone_schedule ems USING (project_id, work_package_id, equipment_id, milestone_id)
JOIN dim_project p ON p.project_id=ps.project_id JOIN dim_equipment eq ON eq.equipment_id=ps.equipment_id
JOIN dim_work_package wp ON wp.work_package_id=ps.work_package_id JOIN dim_milestone m ON m.milestone_id=ps.milestone_id
JOIN fact_purchase_order po ON po.purchase_order_id=ems.purchase_order_id JOIN dim_supplier s ON s.supplier_id=po.supplier_id
LEFT JOIN dim_equipment_supplier es ON es.equipment_id=eq.equipment_id AND es.supplier_id=s.supplier_id
LEFT JOIN dim_manufacturing_location ml ON ml.equipment_id=eq.equipment_id AND ml.supplier_id=s.supplier_id
LEFT JOIN dim_logistics_info li ON li.equipment_id=eq.equipment_id AND li.supplier_id=s.supplier_id
WHERE m.milestone_number='7';
