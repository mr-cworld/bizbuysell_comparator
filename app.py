from flask import Flask, render_template, request, redirect, send_file, flash, url_for
from scraper import scrape_listing
import io
import csv
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Global data store
listings_data = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global listings_data
    if request.method == 'POST':
        url = request.form.get('url')
        if not url or 'bizbuysell.com' not in url:
            flash('Please enter a valid BizBuySell listing URL.')
            return redirect(url_for('index'))
        try:
            data = scrape_listing(url)
            listings_data.append(data)
        except Exception as e:
            flash(f'Error scraping listing: {e}')
        return redirect(url_for('index'))
    return render_template('index.html', listings=listings_data)

@app.route('/export/csv')
def export_csv():
    global listings_data
    if not listings_data:
        flash('No data to export.')
        return redirect(url_for('index'))
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=listings_data[0].keys())
    writer.writeheader()
    for row in listings_data:
        writer.writerow(row)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='biz_comparison.csv')

@app.route('/export/xlsx')
def export_xlsx():
    global listings_data
    if not listings_data:
        flash('No data to export.')
        return redirect(url_for('index'))
    df = pd.DataFrame(listings_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='biz_comparison.xlsx')

@app.route('/reset')
def reset():
    global listings_data
    listings_data = []
    flash('Session reset. All listings cleared.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 