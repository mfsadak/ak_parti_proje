# AK Parti Dinamik Puanlama Sistemi - Web Backend

Bu klasör, AK Parti 81 İl Puanlama Sisteminin web uyumlu backend'ini içerir.

## 🚀 Kurulum

### 1. Gereksinimler
```bash
cd web
pip install -r requirements.txt
```

### 2. Çevre Değişkenleri
`env_example.txt` dosyasını `.env` olarak kopyalayın ve düzenleyin:
```bash
cp env_example.txt .env
```

### 3. Çalıştırma
```bash
python app.py
```

Web arayüzü: http://localhost:5000

## 📁 Klasör Yapısı

```
web/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── env_example.txt       # Environment variables example
├── templates/
│   └── index.html        # Ana web arayüzü
├── static/               # CSS, JS, images
├── uploads/              # Yüklenen CSV dosyaları
└── README.md            # Bu dosya
```

## 🔧 API Endpoints

### Dosya Yükleme
- **POST** `/api/upload`
- CSV dosyalarını yükler
- Multipart form data

### Analiz Başlatma
- **POST** `/api/analyze`
- JSON: `{"openai_api_key": "optional"}`

### Yeni Aktivite
- **POST** `/api/new-activity`
- JSON: `{"activity_name": "string", "coefficient": float}`

### Rapor İndirme
- **GET** `/api/download/<report_type>`
- report_type: "general" veya "coefficients"

### Session Bilgisi
- **GET** `/api/session-info`
- Mevcut session durumu

## 🎯 Özellikler

### ✅ Web Uyumlu
- Drag & Drop dosya yükleme
- Real-time progress gösterimi
- Responsive tasarım
- Session yönetimi

### ✅ Güvenli
- Secure filename handling
- File type validation
- Session-based isolation
- Environment variables

### ✅ Kullanıcı Dostu
- Bootstrap 5 UI
- Font Awesome icons
- Modal dialogs
- Progress indicators

### ✅ API Entegrasyonu
- OpenAI API key web'den girilebilir
- Claude ile dinamik metodoloji
- Hata yönetimi

## 🌐 Production Deployment

### Docker ile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

### Nginx ile
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Environment Variables
Production'da mutlaka ayarlayın:
- `FLASK_SECRET_KEY`: Güvenli bir anahtar
- `FLASK_ENV`: "production"
- `OPENAI_API_KEY`: OpenAI API anahtarı (opsiyonel)

## 🔒 Güvenlik Notları

1. **API Key'i** kodda hardcode etmeyin
2. **File upload** limitlerini ayarlayın
3. **Session timeout** ekleyin
4. **HTTPS** kullanın (production)
5. **Input validation** yapın

## 🐛 Troubleshooting

### Port 5000 kullanımda
```bash
python -c "import os; os.environ['PORT'] = '8080'; exec(open('app.py').read())"
```

### Memory issues
- `MAX_FILE_SIZE` azaltın
- Session cleanup ekleyin

### OpenAI API errors
- API key'i kontrol edin
- Rate limiting ekleyin

## 📞 Destek

Sorunlar için issue açın veya pull request gönderin.
