from pydantic import BaseModel
from typing import List, Optional, Union
from fastapi import APIRouter
from components.db import fetch_all


router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    responses: List[str]
    step: Union[int, float]
    lookup_type: Optional[str] = None
    selected_ticket_id: Optional[str] = None
    selected_site_id: Optional[int] = None


sessions = {}


def get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "step": 1,
            "lookup_type": None,
            "selected_ticket_id": None,
            "selected_site_id": None,
            "last_results": []
        }
    return sessions[session_id]


def reset_session(session):
    session["step"] = 1
    session["lookup_type"] = None
    session["selected_ticket_id"] = None
    session["selected_site_id"] = None
    session["last_results"] = []


BASE_SELECT = """
    SELECT
        s.ticket_id AS ticket_id,
        s.id AS site_id,
        s.site_name AS site_name,
        s.enode AS enode,
        p.projects AS project_code,
        s.est_comp_date AS est_completion_date,
        latest_inv.invoice_amount AS invoice_amount,
        DATE_FORMAT(latest_inv.invoice_date, '%m-%d-%Y') AS invoice_date
    FROM site s
    LEFT JOIN projects p
        ON s.project_id = p.id
    LEFT JOIN (
        SELECT
            b.site_id,
            inv.invoice_amount,
            inv.invoice_date
        FROM billing b
        LEFT JOIN po_invoice inv
            ON inv.id = b.po_inv_id
        WHERE b.po_inv_id IS NOT NULL
    ) latest_inv
        ON latest_inv.site_id = s.id
"""

def get_by_ticket_id(ticket_id: str):
    query = BASE_SELECT + """
        WHERE s.ticket_id = %s
        ORDER BY s.id DESC
        LIMIT 20
    """
    return fetch_all(query, (ticket_id,))


def get_by_site_name(site_name: str):
    query = BASE_SELECT + """
        WHERE LOWER(TRIM(s.site_name)) = LOWER(TRIM(%s))
           OR LOWER(TRIM(s.enode)) = LOWER(TRIM(%s))
        ORDER BY s.id DESC
        LIMIT 20
    """
    return fetch_all(query, (site_name, site_name))


def get_by_project_code(project_code: str):
    query = BASE_SELECT + """
        WHERE LOWER(TRIM(p.projects)) = LOWER(TRIM(%s))
        ORDER BY s.id DESC
        LIMIT 20
    """
    return fetch_all(query, (project_code,))


def get_po_list_by_site_id(site_id: int):
    query = """
        SELECT
            po.po_number,
            po.po_amount
        FROM site s
        INNER JOIN po
            ON po.project_id = s.project_id
           AND po.site_id = s.id
        WHERE s.id = %s
        ORDER BY po.id DESC
    """
    return fetch_all(query, (site_id,))


@router.get("/po_list")
def po_list(site_id: int):
    data = get_po_list_by_site_id(site_id)

    return {
        "site_id": site_id,
        "message": "PO data found" if data else "No PO data found",
        "po_list": data
    }


def value_or_na(value):
    if value is None or value == "":
        return "N/A"
    return value


def po_link_label(site_id):
    return (
        "Kindly click on below link to find PO Amount and PO Number\n"
        "🔗 https://integermobile.com/po_list"
    )


def format_record(row):
    site_id = row.get("site_id")

    return (
        f"✅ Record Found\n"
        f"🎫 Ticket ID: {value_or_na(row.get('ticket_id'))}\n"
        f"🆔 Site ID: {value_or_na(site_id)}\n"
        # f"🏢 Site Name: {value_or_na(row.get('site_name'))}\n"
        f"📡 Site Name: {value_or_na(row.get('enode'))}\n"
        f"📦 Project Code: {value_or_na(row.get('project_code'))}\n"
        f"📅 EST Completion Date: {value_or_na(row.get('est_completion_date'))}\n"
        f"🧾 Invoice Amount: {value_or_na(row.get('invoice_amount'))}\n"
        f"📅 Invoice Date: {value_or_na(row.get('invoice_date'))}\n"
        f"💰 PO Amount / 🔢 PO Number: {po_link_label(site_id)}"
    )


def process_chat(query: str, session_id: str):
    session = get_session(session_id)
    user_query = query.strip()
    user_query_lower = user_query.lower()
    responses = []

    if session["step"] == 1:
        if user_query_lower in ["ticket id", "ticket", "yes"]:
            session["lookup_type"] = "ticket_id"
            session["step"] = 2
            responses.append("✅ Please enter Ticket ID")

        elif user_query_lower in ["site name", "site", "no"]:
            session["lookup_type"] = "site_name"
            session["step"] = 2
            responses.append("✅ Please enter Site Name")

        elif user_query_lower in ["project code", "project", "project name"]:
            session["lookup_type"] = "project_code"
            session["step"] = 2
            responses.append("✅ Please enter Project Code")

        else:
            responses.append("❓ Please enter Ticket ID")

    elif session["step"] == 2:
        lookup_type = session.get("lookup_type")
        results = []

        if lookup_type == "ticket_id":
            results = get_by_ticket_id(user_query)

        elif lookup_type == "site_name":
            results = get_by_site_name(user_query)

        elif lookup_type == "project_code":
            results = get_by_project_code(user_query)

        if results:
            session["last_results"] = results
            first = results[0]
            session["selected_ticket_id"] = first.get("ticket_id")
            session["selected_site_id"] = first.get("site_id")

            if len(results) > 1:
                responses.append(f"✅ Found {len(results)} record(s). Showing top matches:")
                for row in results[:10]:
                    responses.append(format_record(row))
            else:
                responses.append(format_record(first))

            session["step"] = 3

        else:
            responses.append("❌ No record found")
            session["step"] = 3

    elif session["step"] == 3:
        if user_query_lower in ["yes", "new search", "search again"]:
            reset_session(session)
            responses.append("🔄 New search started")
            responses.append("Do you have Ticket ID?")

        elif user_query_lower == "summary":
            if session["last_results"]:
                if len(session["last_results"]) > 1:
                    responses.append(f"📋 Showing {min(len(session['last_results']), 10)} record(s):")
                    for row in session["last_results"][:10]:
                        responses.append(format_record(row))
                else:
                    responses.append(format_record(session["last_results"][0]))
            else:
                responses.append("❌ No result available")

        else:
            responses.append("Type 'yes' to start new search")

    else:
        reset_session(session)
        responses.append("Do you have Ticket ID?")

    return {
        "responses": responses,
        "step": session["step"],
        "lookup_type": session.get("lookup_type"),
        "selected_ticket_id": session.get("selected_ticket_id"),
        "selected_site_id": session.get("selected_site_id"),
    }