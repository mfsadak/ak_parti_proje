#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AK Parti Dinamik Puanlama Sistemi - Basit Web Backend
Pandas olmadan çalışan test versiyonu
"""

import os
import json
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """API durumu"""
    return jsonify({
        'status': 'active',
        'version': '1.0',
        'timestamp': datetime.now().isoformat(),
        'message': 'AK Parti Puanlama Sistemi Aktif'
    })

@app.route('/api/test')
def test():
    """Test endpoint"""
    return jsonify({
        'success': True,
        'message': 'Sistem çalışıyor!',
        'environment': {
            'python_version': '3.13',
            'flask_version': 'OK',
            'pandas_status': 'Devre dışı (test amaçlı)'
        }
    })

if __name__ == '__main__':
    # Production server for Render.com
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
