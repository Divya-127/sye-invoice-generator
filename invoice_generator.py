import io

from fpdf import FPDF
import locale
from num2words import num2words


class PDF(FPDF):
    def header(self):
        # Logo (placeholder - you can replace with your actual logo)
        pass

    def footer(self):
        # Footer
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')


class InvoiceGenerator:
    def __init__(self, company_info, bill_to, ship_to, invoice_details, products, bank_details):
        self.company_info = company_info
        self.bill_to = bill_to
        self.ship_to = ship_to
        self.invoice_details = invoice_details
        self.products = products
        self.bank_details = bank_details
        self.totals = self.calculate_totals()
        try:
            locale.setlocale(locale.LC_ALL, 'en_IN')
        except:
            locale.setlocale(locale.LC_ALL, '')

    def calculate_totals(self):
        totals = {
            'subtotal': 0,
            'cgst': 0,
            'sgst': 0,
            'igst': 0,
            'total': 0
        }

        for product in self.products:
            product['amount'] = product['quantity'] * product['rate']
            totals['subtotal'] += product['amount']

        # Apply tax based on location
        if self.bill_to['state'].lower() == 'maharashtra':
            totals['cgst'] = round(totals['subtotal'] * 0.09, 2)
            totals['sgst'] = round(totals['subtotal'] * 0.09, 2)
        else:
            totals['igst'] = round(totals['subtotal'] * 0.18, 2)

        totals['total'] = totals['subtotal'] + totals['cgst'] + totals['sgst'] + totals['igst']

        return totals

    def amount_in_words(self, amount):
        try:
            words = num2words(int(amount), lang='en_IN').replace(',', '').title()
            # rupees = int(amount)
            # paise = int(round((amount - rupees) * 100))

            # if paise > 0:
            #     return f"{words} Rupees and {num2words(paise, lang='en_IN').title()} Paise Only"
            # else:
            return f"{words} Rupees Only"
        except:
            # Fallback function in case num2words isn't available or fails
            def num_to_words(num):
                under_20 = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
                            'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen',
                            'Nineteen']
                tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

                if num < 20:
                    return under_20[num]

                if num < 100:
                    return tens[num // 10] + ('' if num % 10 == 0 else ' ' + under_20[num % 10])

                if num < 1000:
                    return under_20[num // 100] + ' Hundred' + (
                        '' if num % 100 == 0 else ' and ' + num_to_words(num % 100))

                if num < 100000:
                    return num_to_words(num // 1000) + ' Thousand' + (
                        '' if num % 1000 == 0 else ' ' + num_to_words(num % 1000))

                if num < 10000000:
                    return num_to_words(num // 100000) + ' Lakh' + (
                        '' if num % 100000 == 0 else ' ' + num_to_words(num % 100000))

                return num_to_words(num // 10000000) + ' Crore' + (
                    '' if num % 10000000 == 0 else ' ' + num_to_words(num % 10000000))

            rupees = int(amount)
            paise = int(round((amount - rupees) * 100))

            result = num_to_words(rupees) + ' Rupees'
            if paise > 0:
                result += ' and ' + num_to_words(paise) + ' Paise'

            return result + ' Only'

    def generate_pdf(self, output_filename="invoice.pdf"):
        pdf = PDF('P', 'mm', 'A4')
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_top_margin(10)  # Reduce top margin slightly

        # Colors
        header_color = (41, 128, 185)  # Blue
        accent_color = (52, 152, 219)  # Light Blue
        text_color = (44, 62, 80)  # Dark Blue/Gray

        # Title
        pdf.set_font('Arial', 'B', 20)
        pdf.set_text_color(*header_color)
        pdf.cell(0, 10, 'TAX INVOICE', 0, 1, 'C')
        pdf.ln(1)  # Reduced spacing further

        # Company details - Left side
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(*text_color)

        # Two-column layout for company and invoice details
        col_width = 95
        y_start = pdf.get_y()

        # Company info - Left column
        pdf.set_xy(10, y_start)
        pdf.cell(col_width, 6, self.company_info['name'], 0, 1, 'L')
        pdf.set_font('Arial', '', 9)
        pdf.set_x(10)
        pdf.multi_cell(col_width, 4, self.company_info['address'], 0, 'L')  # Reduced line height
        pdf.set_x(10)
        pdf.cell(30, 4, f"Contact:", 0, 0, 'L')
        pdf.cell(col_width - 30, 4, self.company_info['contact'], 0, 1, 'L')
        pdf.set_x(10)
        pdf.cell(30, 4, f"Email:", 0, 0, 'L')
        pdf.cell(col_width - 30, 4, self.company_info['email'], 0, 1, 'L')
        pdf.set_font('Arial', 'B', 9)
        pdf.set_x(10)
        pdf.cell(30, 4, f"GSTIN:", 0, 0, 'L')
        pdf.cell(col_width - 30, 4, self.company_info['gstin'], 0, 1, 'L')

        # Invoice details - Right column
        box_y = y_start
        pdf.set_xy(105, box_y)
        pdf.set_fill_color(*accent_color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(95, 6, 'INVOICE DETAILS', 0, 1, 'L', 1)  # Reduced height

        pdf.set_text_color(*text_color)
        pdf.set_font('Arial', '', 9)

        pdf.set_xy(105, pdf.get_y())
        pdf.cell(40, 4, 'Invoice No:', 0, 0, 'L')
        pdf.cell(55, 4, self.invoice_details['number'], 0, 1, 'L')

        pdf.set_xy(105, pdf.get_y())
        pdf.cell(40, 4, 'Date:', 0, 0, 'L')
        pdf.cell(55, 4, self.invoice_details['date'], 0, 1, 'L')

        if self.invoice_details['po_number']:
            pdf.set_xy(105, pdf.get_y())
            pdf.cell(40, 4, 'PO Number:', 0, 0, 'L')
            pdf.cell(55, 4, self.invoice_details['po_number'], 0, 1, 'L')

        pdf.set_xy(105, pdf.get_y())
        pdf.cell(40, 4, 'Transport:', 0, 0, 'L')
        pdf.cell(55, 4, self.invoice_details['transport'], 0, 1, 'L')

        # Reset to full width, finding the max Y position
        pdf.set_xy(10, max(pdf.get_y(), box_y + 30))  # Reduced height
        pdf.ln(3)  # Reduced spacing

        # Customer details - side by side layout
        pdf.set_fill_color(*accent_color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(95, 6, 'BILL TO', 0, 0, 'L', 1)  # Reduced height
        pdf.cell(5, 6, '', 0, 0)
        pdf.cell(95, 6, 'SHIP TO', 0, 1, 'L', 1)

        y_position = pdf.get_y()

        # Bill to details
        pdf.set_text_color(*text_color)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(95, 4, self.bill_to['name'], 0, 1, 'L')
        pdf.set_font('Arial', '', 9)
        pdf.multi_cell(95, 4, self.bill_to['address'], 0, 'L')  # Reduced line height
        pdf.cell(95, 4, self.bill_to['state'], 0, 1, 'L')
        pdf.cell(30, 4, 'Contact:', 0, 0, 'L')
        pdf.cell(65, 4, self.bill_to['contact'], 0, 1, 'L')
        pdf.cell(30, 4, 'GSTIN:', 0, 0, 'L')
        pdf.cell(65, 4, self.bill_to['gstin'], 0, 1, 'L')

        # Ship to details
        ship_height = pdf.get_y() - y_position
        pdf.set_xy(110, y_position)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(95, 4, self.ship_to['name'], 0, 1, 'L')
        pdf.set_font('Arial', '', 9)
        pdf.set_xy(110, pdf.get_y())
        pdf.multi_cell(95, 4, self.ship_to['address'], 0, 'L')  # Reduced line height
        pdf.set_xy(110, pdf.get_y())
        pdf.cell(95, 4, self.ship_to['state'], 0, 1, 'L')
        pdf.set_xy(110, pdf.get_y())
        pdf.cell(30, 4, 'Contact:', 0, 0, 'L')
        pdf.cell(65, 4, self.ship_to['contact'], 0, 1, 'L')
        pdf.set_xy(110, pdf.get_y())
        pdf.cell(30, 4, 'GSTIN:', 0, 0, 'L')
        pdf.cell(65, 4, self.ship_to['gstin'], 0, 1, 'L')

        # Reset position to after both columns
        pdf.set_xy(10, y_position + ship_height)
        pdf.ln(3)  # Reduced spacing

        # Product table - with drum size column
        pdf.set_fill_color(*header_color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 9)

        # Adjust column widths to accommodate drum size
        col_widths = [10, 65, 20, 25, 15, 25, 30]
        pdf.cell(col_widths[0], 6, 'S.No', 1, 0, 'C', 1)  # Reduced height
        pdf.cell(col_widths[1], 6, 'Name & Description', 1, 0, 'C', 1)
        pdf.cell(col_widths[2], 6, 'HSN Code', 1, 0, 'C', 1)
        pdf.cell(col_widths[3], 6, 'Drum Size', 1, 0, 'C', 1)  # New column for drum size
        pdf.cell(col_widths[4], 6, 'Qty', 1, 0, 'C', 1)
        pdf.cell(col_widths[5], 6, 'Rate', 1, 0, 'C', 1)
        pdf.cell(col_widths[6], 6, 'Amount', 1, 1, 'C', 1)

        # Product items
        pdf.set_text_color(*text_color)
        pdf.set_font('Arial', '', 9)

        for i, product in enumerate(self.products, 1):
            pdf.cell(col_widths[0], 6, str(i), 1, 0, 'C')  # Reduced height
            pdf.cell(col_widths[1], 6, product['name'], 1, 0, 'L')
            pdf.cell(col_widths[2], 6, product['hsn'], 1, 0, 'C')
            pdf.cell(col_widths[3], 6, product.get('drum_size', 'N/A'), 1, 0, 'C')  # Display drum size
            pdf.cell(col_widths[4], 6, str(product['quantity']), 1, 0, 'C')
            pdf.cell(col_widths[5], 6, f"{product['rate']:,.2f}", 1, 0, 'R')
            pdf.cell(col_widths[6], 6, f"{product['amount']:,.2f}", 1, 1, 'R')

        # Summary table - cleaner layout
        total_width = sum(col_widths[:6])
        amount_width = col_widths[6]

        pdf.cell(total_width, 6, 'Subtotal', 1, 0, 'R')  # Reduced height
        pdf.cell(amount_width, 6, f"{self.totals['subtotal']:,.2f}", 1, 1, 'R')

        if self.bill_to['state'].lower() == 'maharashtra':
            pdf.cell(total_width, 6, 'CGST @ 9%', 1, 0, 'R')
            pdf.cell(amount_width, 6, f"{self.totals['cgst']:,.2f}", 1, 1, 'R')

            pdf.cell(total_width, 6, 'SGST @ 9%', 1, 0, 'R')
            pdf.cell(amount_width, 6, f"{self.totals['sgst']:,.2f}", 1, 1, 'R')
        else:
            pdf.cell(total_width, 6, 'IGST @ 18%', 1, 0, 'R')
            pdf.cell(amount_width, 6, f"{self.totals['igst']:,.2f}", 1, 1, 'R')

        # Total
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(*header_color)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(total_width, 6, 'TOTAL', 1, 0, 'R', 1)  # Reduced height
        pdf.cell(amount_width, 6, f"{self.totals['total']:,.2f}", 1, 1, 'R', 1)

        pdf.set_text_color(*text_color)
        pdf.set_font('Arial', 'I', 10)
        pdf.ln(1)
        pdf.cell(0, 5, f"Amount in words: {self.amount_in_words(self.totals['total'])}", 0, 1, 'L')

        # Terms and Conditions - more compact
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(*accent_color)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 6, 'TERMS AND CONDITIONS', 0, 1, 'L', 1)

        pdf.set_text_color(*text_color)
        pdf.set_font('Arial', '', 8)  # Smaller font

        # Even more compact terms
        terms = [
            "1. Payment due within 30 days of invoice date. Late payments subject to 1.5% interest per month.",
            "2. Goods once sold will not be taken back. Our responsibility ceases upon delivery.",
            "3. Subject to local jurisdiction only."
        ]

        for term in terms:
            pdf.cell(0, 4, term, 0, 1, 'L')

        # Bank details section - now below terms and conditions
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(*accent_color)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 6, 'BANK DETAILS', 0, 1, 'L', 1)

        pdf.set_text_color(*text_color)
        pdf.set_font('Arial', '', 9)

        # Create a two-column layout for bank details to save space
        col_width = 95

        # First row
        pdf.cell(40, 4, 'Bank Name:', 0, 0, 'L')
        pdf.cell(col_width - 40, 4, self.bank_details['bank_name'], 0, 0, 'L')
        pdf.cell(40, 4, 'Account Name:', 0, 0, 'L')
        pdf.cell(col_width - 40, 4, self.bank_details['account_name'], 0, 1, 'L')

        # Second row
        pdf.cell(40, 4, 'Account Number:', 0, 0, 'L')
        pdf.cell(col_width - 40, 4, self.bank_details['account_number'], 0, 0, 'L')
        pdf.cell(40, 4, 'IFSC Code:', 0, 0, 'L')
        pdf.cell(col_width - 40, 4, self.bank_details['ifsc_code'], 0, 1, 'L')

        # Third row (single column for branch)
        pdf.cell(40, 4, 'Branch:', 0, 0, 'L')
        pdf.cell(col_width - 40, 4, self.bank_details['branch'], 0, 1, 'L')

        # Signature - ensure it stays on first page
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 5, f"For {self.company_info['name']}", 0, 1, 'R')

        pdf.ln(6)  # Reduced space for signature
        pdf.cell(0, 5, "Authorized Signatory", 0, 1, 'R')

        # Save the PDF
        if isinstance(output_filename, io.BytesIO):
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            output_filename.write(pdf_bytes)
        else:
            pdf.output(output_filename)

        return output_filename