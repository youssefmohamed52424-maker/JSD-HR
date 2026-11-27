import frappe
from frappe import _
from frappe.utils import nowdate


def create_additional_salary_from_action(doc, method):
	"""Upon approval/submission of Bonus or Deduction, push automatically to Additional Salary"""
	if doc.salary_slip_created:
		return

	component = (
		"Performance & Site Visit Bonus"
		if doc.action_type == "Bonus"
		else "Administrative Deductions"
	)

	add_sal = frappe.get_doc({
		"doctype": "Additional Salary",
		"employee": doc.employee,
		"salary_component": component,
		"amount": doc.amount,
		"payroll_date": doc.payroll_date or nowdate(),
		"overwrite_salary_structure_amount": 0,
		"ref_doctype": doc.doctype,
		"ref_docname": doc.name,
	})
	add_sal.insert(ignore_permissions=True)
	add_sal.submit()
	doc.db_set("salary_slip_created", 1)


def push_commission_to_payroll(doc, method):
	"""Upon submission of Commission Log, push automatically to Additional Salary"""
	if doc.status == "Pushed to Payroll":
		return

	add_sal = frappe.get_doc({
		"doctype": "Additional Salary",
		"employee": doc.employee,
		"salary_component": "Real Estate Sales Commission",
		"amount": doc.commission_amount,
		"payroll_date": doc.payroll_date or nowdate(),
		"overwrite_salary_structure_amount": 0,
		"ref_doctype": doc.doctype,
		"ref_docname": doc.name,
	})
	add_sal.insert(ignore_permissions=True)
	add_sal.submit()
	doc.db_set("status", "Pushed to Payroll")


def generate_commissions_from_contract(doc, method):
    """DEAL-06 / COM-04: Auto-create Commission Logs when Contract is Completed and Down Payment is Paid."""
    if doc.commissions_pushed:
        return

    is_completed = "Contract Completed" in (doc.contract_status or "")
    if not (is_completed and doc.down_payment_paid):
        return

    contract_val = float(doc.contract_value or 0)
    if contract_val <= 0:
        return

    # 1. حساب عمولة المبيعات الأساسية وتقسيم تغيير الوش (Change Faces)
    total_sales_comm = contract_val * (float(doc.primary_commission_rate or 0) / 100.0)
    comm_type_label = (
        "Resale / Partner (شراكة / إعادة بيع)"
        if "Resale" in (doc.commission_category or "")
        else "Pure Leads (مبيعات مباشرة)"
    )

    if total_sales_comm > 0 and doc.primary_employee:
        if doc.is_change_faces and doc.secondary_employee:
            sec_ratio = float(doc.secondary_split_percent or 50) / 100.0
            sec_amount = round(total_sales_comm * sec_ratio, 2)
            pri_amount = round(total_sales_comm - sec_amount, 2)

            if pri_amount > 0:
                _insert_commission_log(doc.primary_employee, comm_type_label, doc.name, pri_amount)
            if sec_amount > 0:
                _insert_commission_log(doc.secondary_employee, comm_type_label, doc.name, sec_amount)
        else:
            _insert_commission_log(doc.primary_employee, comm_type_label, doc.name, round(total_sales_comm, 2))

    # 2. حساب عمولة إشراف مدير المبيعات (Sales Manager Override)
    mgr_rate = float(doc.manager_commission_rate or 0)
    if doc.sales_manager_employee and mgr_rate > 0:
        mgr_amount = round(contract_val * (mgr_rate / 100.0), 2)
        if mgr_amount > 0:
            _insert_commission_log(
                doc.sales_manager_employee,
                "Sales Manager Override (إشراف مبيعات)",
                doc.name,
                mgr_amount,
            )

    # 3. تحديث حالة الوحدة إلى مباعة (HOLD-06)
    if doc.unit and frappe.db.exists("JSD Unit", doc.unit):
        unit_meta = frappe.get_meta("JSD Unit")
        if unit_meta.has_field("status"):
            frappe.db.set_value("JSD Unit", doc.unit, "status", "Sold")

    doc.db_set("commissions_pushed", 1)


def _insert_commission_log(employee, commission_type, contract_ref, amount):
    log = frappe.get_doc({
        "doctype": "JSD Sales Commission Log",
        "employee": employee,
        "commission_type": commission_type,
        "contract_reference": contract_ref,
        "commission_amount": amount,
        "payroll_date": nowdate(),
    })
    log.insert(ignore_permissions=True)
    log.submit()
