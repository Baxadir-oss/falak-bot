# Falak — Ob-havo boti

Sizning "ObHavo Bot Professional Reja v3" hujjatingiz asosida yozilgan,
ishga tushirishga tayyor loyiha. Quyida — noldan (server sotib olishdan)
to botni ishga tushirishgacha bo'lgan barcha qadamlar, siz mobil qurilmadan
ishlaydigan bo'lsangiz ham bajara oladigan tartibda.

## 1. Loyiha strukturasi

```
falak-bot/
├── app/
│   ├── main.py              # Kirish nuqtasi (aiogram + FastAPI bitta jarayonda)
│   ├── config.py            # .env'dan o'qiladigan sozlamalar
│   ├── bot/                 # Telegram bot handler'lari, klaviaturalar, FSM
│   ├── services/             # DB, kesh, Open-Meteo klient, i18n, formatlash
│   ├── locales/              # uz/ru/en/kk tarjima fayllari
│   └── data/                 # WMO ob-havo kodlari, Falak Hikmati matnlari
├── deploy/
│   ├── falak-bot.service     # systemd xizmat fayli
│   ├── nginx.conf.example    # HTTPS teskari proksi namunasi
│   └── setup.sh              # avtomatik o'rnatish skripti
├── miniapp/
│   └── index.html            # Mini App (Cloudflare Pages'ga joylashtiriladi)
├── requirements.txt
└── .env.example
```

**Muhim: bu MVP (1-bosqich) + kunlik bildirishnoma.** Oylik statistika,
tendensiya tahlili va Mini App'ning to'liq animatsiyali dizayni (7-8-bo'lim,
2-bosqich) keyingi safar qo'shiladi.

## 2. Kerakli narsalar

- **VPS**: Ubuntu 22.04/24.04, kamida 512MB RAM (reja 1.1-bo'limiga mos).
  Hetzner CX11, Timeweb, yoki shunga o'xshash arzon variant yetarli.
- **Domen**: Telegram webhook faqat HTTPS + haqiqiy domen bilan ishlaydi
  (IP orqali ishlamaydi). Domenni VPS IP'siga A-record bilan yo'naltiring.
- **Bot tokeni**: Telegram'da [@BotFather](https://t.me/BotFather) orqali
  `/newbot` bilan yarating, tokenni saqlab qo'ying.
- Mobil qurilmadan SSH ulanish uchun **Termux** (Android) yoki **Termius**
  kabi ilova.

## 3. Kodni serverga yuklash

Siz mobil qurilmadan ishlaganingiz uchun, eng qulay yo'l — kodni avval
GitHub'ga yuklab, so'ng serverda `git clone` qilish:

1. GitHub'da yangi **private** repozitoriy yarating (masalan `falak-bot`).
2. Ushbu papkadagi barcha fayllarni o'sha repozitoriyga yuklang (drag-and-drop
   yoki GitHub mobil ilovasi orqali — bir martalik ish).
3. Serverga SSH orqali kiring, so'ng:

```bash
git clone https://github.com/FOYDALANUVCHI_NOMINGIZ/falak-bot.git
cd falak-bot
```

## 4. O'rnatish

```bash
bash deploy/setup.sh
```

Bu skript avtomatik ravishda: kerakli tizim paketlarini (`nginx`, `certbot`,
`python3-venv`) o'rnatadi, virtual muhit yaratadi, `requirements.txt`ni
o'rnatadi, `.env.example`dan `.env` yaratadi va systemd xizmatini sozlaydi.

## 5. `.env` faylini to'ldirish

```bash
nano .env
```

Kamida quyidagilarni to'ldiring:

| O'zgaruvchi | Qiymat |
|---|---|
| `BOT_TOKEN` | BotFather bergan token |
| `WEBHOOK_BASE_URL` | `https://sizning-domeningiz.uz` |
| `WEBHOOK_SECRET` | Tasodifiy uzun qator — terminalda: `openssl rand -hex 32` |

## 6. Domen, HTTPS va nginx

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/falak-bot
sudo nano /etc/nginx/sites-available/falak-bot   # domain.uz'ni o'zingiznikiga almashtiring
sudo ln -s /etc/nginx/sites-available/falak-bot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d sizning-domeningiz.uz
```

Certbot HTTPS sertifikatini avtomatik oladi va nginx konfiguratsiyasiga
qo'shadi.

## 7. Botni ishga tushirish

```bash
sudo systemctl enable --now falak-bot
sudo systemctl status falak-bot
```

Agar `active (running)` ko'rinsa — ishga tushdi. Loglarni ko'rish:

```bash
journalctl -u falak-bot -f
```

Tekshirish uchun brauzerda oching: `https://sizning-domeningiz.uz/health`
— `{"status": "ok"}` chiqishi kerak.

Endi Telegram'da botingizga `/start` yuboring.

## 8. Mini App'ni joylashtirish (ixtiyoriy, keyinroq ham qilsa bo'ladi)

1. `miniapp/index.html` faylidagi `API_BASE` o'zgaruvchisini o'zingizning
   domeningizga almashtiring.
2. Bu faylni [Cloudflare Pages](https://pages.cloudflare.com)ga yuklang
   (GitHub repozitoriyni ulash orqali eng oson — drag-and-drop qilish
   ham mumkin).
3. BotFather'da: `/mybots` → botingizni tanlang → **Bot Settings** →
   **Menu Button** → Cloudflare Pages bergan URL'ni kiriting.
4. `.env` dagi `CORS_ORIGINS`ga shu Cloudflare Pages manzilini yozib,
   botni qayta ishga tushiring: `sudo systemctl restart falak-bot`.

## 9. Nima ishlaydi, nima hali yo'q

**Ishlaydi (shu versiyada):**
- 4 tilli (uz/ru/en/kk) til tanlash
- Joylashuvni ulashish yoki qo'lda shahar qidirish
- Bugungi ob-havo (harorat, his qilinish, namlik, shamol, UV, quyosh
  chiqishi/botishi) va 7 kunlik prognoz
- Falak Hikmati — ob-havo holatiga mos kunlik hikmat
- Amaliy tavsiyalar (soyabon, UV himoyasi, shamol, sovuq haqida)
- Kunlik bildirishnoma (foydalanuvchi belgilagan soatda)
- Mini App uchun tayyor `/api/weather` endpoint + boshlang'ich frontend

**Hali yo'q / bilib qo'yish kerak:**
- **Vaqt zonasi**: kunlik bildirishnoma hozircha bitta umumiy vaqt zonasida
  (Asia/Tashkent) ishlaydi — har foydalanuvchi uchun alohida emas.
- **Falak Hikmati matnlari** — bu versiyada men original yozgan namuna
  to'plam (5 toifa × 3 ta, 4 tilda). Ishga tushirishdan oldin ona tilida
  so'zlashuvchi birov ko'rib chiqsa yaxshi bo'lardi — xohlasangiz sonini
  ham oshirsa bo'ladi.
- **Teskari geokodlash** (joylashuv ulashilganda shahar nomini topish)
  uchun BigDataCloud'ning bepul xizmati qo'shildi — rejada bu alohida
  ko'rsatilmagan edi, lekin oqim to'liq ishlashi uchun zarur edi.
- **Mini App dizayni** — bu boshlang'ich, sodda versiya (katta raqam +
  holat + haftalik ro'yxat). Reja 3.1-bo'limidagi to'liq animatsiyali,
  Meteocons bilan boyitilgan versiya keyingi bosqich.
- Oylik statistika/tendensiya (reja 3.4, 2-bosqich) hali yo'q.

## 10. Tez-tez uchraydigan xatolar

- **Webhook o'rnatilmayapti** — `BOT_TOKEN` yoki `WEBHOOK_BASE_URL`
  noto'g'ri, yoki domen hali serverga to'g'ri yo'naltirilmagan.
  `journalctl -u falak-bot -n 50` bilan aniq xato matnini ko'ring.
- **"database is locked"** — bo'lmasligi kerak (WAL yoqilgan), lekin
  agar ko'p nusxa (bir nechta worker) ishga tushirilsa yuzaga kelishi
  mumkin. `--workers 1` bilan cheklab qo'yilgan, o'zgartirmang.
- **Bot javob bermayapti** — avval `/health` ishlayotganini, keyin
  `sudo systemctl status falak-bot` xato bermayotganini tekshiring.
