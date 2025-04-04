from flask import Flask, render_template, request, jsonify, send_file
from invoice_generator import InvoiceGenerator
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

app = Flask(__name__)

# Google Sheets setup
# def get_gsheet():
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
#     return gspread.authorize(creds)

def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    return gspread.authorize(creds)

# Load data from Google Sheet
def load_invoice_data():
    client = get_gsheet()
    workbook = client.open("Invoice-Data-Master")

    company_ws = workbook.worksheet("Company")
    clients_ws = workbook.worksheet("Clients")
    products_ws = workbook.worksheet("Products")

    # Company
    company = dict(zip(company_ws.row_values(1), company_ws.row_values(2)))

    # Clients
    clients = [dict(zip(clients_ws.row_values(1), row)) for row in clients_ws.get_all_values()[1:]]

    # Products
    products = [dict(zip(products_ws.row_values(1), row)) for row in products_ws.get_all_values()[1:]]

    return {
        "company": company,
        "clients": clients,
        "products": products
    }

# Log to Invoice Log sheet
def log_invoice(data):
    client = get_gsheet()
    log_ws = client.open("Invoice-Data-Master").worksheet("Invoice Log")

    total = sum(p['rate'] * p['quantity'] for p in data['products'])

    row = [
        data['invoice']['number'],
        data['invoice']['date'],
        data['bill_to']['name'],
        data['bill_to']['gstin'],
        data['invoice']['transport'],
        f"{total:.2f}"
    ]
    log_ws.append_row(row)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    return jsonify(load_invoice_data())

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()

    buffer = io.BytesIO()
    invoice = InvoiceGenerator(
        company_info=data["company"],
        bill_to=data["bill_to"],
        ship_to=data["ship_to"],
        invoice_details=data["invoice"],
        products=data["products"],
        bank_details=data["bank"]
    )
    invoice.generate_pdf(output_filename=buffer)
    buffer.seek(0)

    print("PDF size:", len(buffer.getvalue()), "bytes")

    # Optional: Log to Google Sheet here
    log_invoice(data)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{data['invoice']['number']}.pdf"
    )


if __name__ == "__main__":
    app.run(debug=False)
