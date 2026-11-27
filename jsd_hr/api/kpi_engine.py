import frappe
from frappe.utils import nowdate, add_months, getdate

def evaluate_monthly_kpis():
    if not frappe.db.exists("DocType", "JSD KPI Settings"):
        return
    settings = frappe.get_single("JSD KPI Settings")
    visits_target = getattr(settings, "monthly_site_visits_target", 5) or 5
    grace_months = getattr(settings, "evaluation_period_months", 3) or 3
    bonus_amount = getattr(settings, "target_exceeded_bonus", 0) or 0

    employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name", "user_id"])
    for emp in employees:
        if not emp.user_id:
            continue
        # حساب المعاينات والعملاء المسندين خلال الشهر الحالي
        month_start = getdate(nowdate()).replace(day=1)
        assigned_leads = frappe.db.count("Lead", {"lead_owner": emp.user_id, "creation": [">=", month_start]})
        contacted_leads = frappe.db.count("Lead", {"lead_owner": emp.user_id, "status": ["!=", "Lead"], "creation": [">=", month_start]})
        site_visits = frappe.db.count("Event", {"owner": emp.user_id, "subject": ["like", "%معاينة%"], "starts_on": [">=", month_start]})

        # مكافأة تجاوز مستهدف المعاينات تلقائياً
        if site_visits > visits_target and bonus_amount > 0:
            if not frappe.db.exists("JSD HR Action Request", {"employee": emp.name, "action_type": "Reward", "reason": ["like", "%تجاوز مستهدف المعاينات%"], "creation": [">=", month_start]}):
                frappe.get_doc({
                    "doctype": "JSD HR Action Request",
                    "employee": emp.name,
                    "action_type": "Reward",
                    "amount": bonus_amount,
                    "reason": f"مكافأة تلقائية: تجاوز مستهدف المعاينات ({site_visits} من أصل {visits_target})"
                }).insert(ignore_permissions=True)

        # تنبيه للـ HR والعمليات عند استمرار التقصير
        if assigned_leads > 0 and (contacted_leads / assigned_leads) < 0.5 and site_visits < visits_target:
            hr_users = frappe.get_all("Has Role", filters={"role": "HR Manager", "parenttype": "User"}, pluck="parent")
            for hr_user in hr_users:
                frappe.get_doc({
                    "doctype": "Notification Log",
                    "subject": f"تنبيه KPI: تقصير الموظف {emp.employee_name} في المعاينات ومتابعة العملاء",
                    "for_user": hr_user,
                    "type": "Alert"
                }).insert(ignore_permissions=True)
