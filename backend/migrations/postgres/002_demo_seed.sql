-- Deterministic demo seed for a clean TheManager Aurora deployment.
INSERT INTO dim_project (project_code, project_name, project_country, project_location) VALUES ('100000', 'Project A', 'Germany', 'Regensburg') ON CONFLICT (project_code) DO NOTHING;
INSERT INTO dim_work_package (work_package_code, work_package_name, wbs) VALUES ('F12', 'Low Voltage / Power', 'S-100000-2-67-F12') ON CONFLICT (work_package_code) DO NOTHING;
INSERT INTO dim_equipment (equipment_code, equipment_name, equipment_type) VALUES ('123456', 'LV Switchgear 1', 'Electrical'), ('123457', 'LV Switchgear 2', 'Electrical'), ('123458', 'LV Switchgear 3', 'Electrical') ON CONFLICT (equipment_code) DO NOTHING;
INSERT INTO dim_milestone (milestone_number, milestone_activity, milestone_description) VALUES ('7', 'Delivery to Site', 'Demo delivery milestone') ON CONFLICT (milestone_activity, milestone_description) DO NOTHING;
INSERT INTO dim_supplier (supplier_number, supplier_name, email_address) VALUES ('111111', 'Company A', 'supplier@example.com') ON CONFLICT (supplier_number) DO NOTHING;

INSERT INTO fact_purchase_order (purchase_order_number, line_item, project_id, work_package_id, supplier_id, equipment_id, amount)
SELECT 'PO0001', equipment.equipment_code, project.project_id, package.work_package_id, supplier.supplier_id, equipment.equipment_id, 85000
FROM dim_project project CROSS JOIN dim_work_package package CROSS JOIN dim_supplier supplier JOIN dim_equipment equipment ON equipment.equipment_code IN ('123456', '123457', '123458')
WHERE project.project_code='100000' AND package.work_package_code='F12' AND supplier.supplier_number='111111'
ON CONFLICT (purchase_order_number, line_item) DO NOTHING;
