import frappe
from frappe import _

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{"fieldname": "employee", "label": _("Employee ID"), "fieldtype": "Link", "options": "Employee", "width": 120},
		{"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data", "width": 200},
		{"fieldname": "custom_employment_category", "label": _("Category"), "fieldtype": "Data", "width": 180},
		{"fieldname": "custom_bank", "label": _("Bank Name"), "fieldtype": "Link", "options": "Bank", "width": 150},
		{"fieldname": "custom_bank_account_iban", "label": _("Bank Account / IBAN"), "fieldtype": "Data", "width": 210},
		{"fieldname": "gross_pay", "label": _("Gross Pay"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_deduction", "label": _("Total Deduction"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "net_pay", "label": _("Net Transfer Amount"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "salary_slip", "label": _("Salary Slip"), "fieldtype": "Link", "options": "Salary Slip", "width": 140}
	]

def get_data(filters):
	conditions = ["ss.docstatus = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("ss.start_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("ss.end_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("bank"):
		conditions.append("emp.custom_bank = %(bank)s")
		values["bank"] = filters["bank"]
	if filters.get("employment_category"):
		conditions.append("emp.custom_employment_category = %(employment_category)s")
		values["employment_category"] = filters["employment_category"]

	where_clause = " AND ".join(conditions)

	return frappe.db.sql(f"""
		SELECT
			ss.employee,
			ss.employee_name,
			emp.custom_employment_category,
			emp.custom_bank,
			emp.custom_bank_account_iban,
			ss.gross_pay,
			ss.total_deduction,
			ss.net_pay,
			ss.name AS salary_slip
		FROM `tabSalary Slip` ss
		LEFT JOIN `tabEmployee` emp ON emp.name = ss.employee
		WHERE {where_clause}
		ORDER BY emp.custom_bank ASC, ss.employee_name ASC
	""", values, as_dict=True)
