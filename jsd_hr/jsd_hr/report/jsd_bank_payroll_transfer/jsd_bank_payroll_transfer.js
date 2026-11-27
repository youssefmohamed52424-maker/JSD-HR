frappe.query_reports["JSD Bank Payroll Transfer"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_end(),
			"reqd": 1
		},
		{
			"fieldname": "bank",
			"label": __("Bank"),
			"fieldtype": "Link",
			"options": "Bank"
		},
		{
			"fieldname": "employment_category",
			"label": __("Employment Category"),
			"fieldtype": "Select",
			"options": "\nInsured Employee (موظف رسمي - مؤمن عليه)\nIntern / Student (متدرب / طالب)"
		}
	]
};
