from datetime import date, datetime , timezone
from decimal import Decimal
from typing import Any, Optional , List
from pydantic import BaseModel,Field,ConfigDict, EmailStr

"""Tüm tip kontratları"""

class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@hotelmind.ai"])
    password: str = Field(..., min_length=6, description="Ham kullanıcı şifresi")

class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., examples=["admin@hotelmind.ai"])
    password: str = Field(..., min_length=8, description="En az 8 karakterli güçlü şifre")
    full_name: str = Field(..., min_length=2, max_length=100)
    hotel_id: Optional[str] = Field(None, description="Otel yöneticisi/çalışanıysa bağlı olduğu otel ID")
# 2. İstemciye dönülecek Opaque Token yanıt DTO'su
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="opq_ ile başlayan referans token")
    token_type: str = Field(default="Bearer")
    expires_in: int = Field(default=86400, description="Saniye cinsinden geçerlilik süresi (24 saat)")

# 3. Redis'te saklanan ve servislerin tüketeceği Session Context DTO'su
class SessionPayload(BaseModel):
    user_id: str = Field(..., description="Kullanıcı UUID'si")
    email: EmailStr
    role: str = Field(default="user", description="Kullanıcı rolü (admin, user vb.)")
    scopes: List[str] = Field(default_factory=list, description="Yetki listesi")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: int = Field(..., description="Epoch timestamp")
    model_config = ConfigDict(frozen=True)

# 1. Yeni Kullanıcı Kaydı (Sign-Up)
class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., examples=["admin@hotelmind.ai"])
    password: str = Field(..., min_length=8, description="En az 8 karakterli güçlü şifre")
    full_name: str = Field(..., min_length=2, max_length=100)
    hotel_id: Optional[str] = Field(None, description="Otel yöneticisi/çalışanıysa bağlı olduğu otel ID")


# 2. Şifresiz/Güvenli Kullanıcı Profil Yanıtı (GET /me veya Register sonrası)
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    hotel_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 3. Şifre Değiştirme (Giriş Yapmış Kullanıcı İçin)
class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)

# 4. Şifre Sıfırlama (Forgot / Reset Password Akışı)
class PasswordResetInitRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., description="E-postaya gönderilen tek kullanımlık reset token")
    new_password: str = Field(..., min_length=8)


# 5. Tüm Cihazlardan Çıkış / Belirli Oturumu İptal Etme
class RevokeSessionRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Boş bırakılırsa tüm oturumları, doluysa spesifik oturumu siler")


# 6. Servisler Arası Standart Hata Sözleşmesi
class ErrorDetail(BaseModel):
    code: str = Field(..., description="Hata kodu (örn: INVALID_CREDENTIALS, SESSION_EXPIRED)")
    message: str = Field(..., description="İnsan tarafından okunabilir hata mesajı")
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail 
    
#Response Service
class PriceQueryRequest(BaseModel):
    hotel_id: str = Field(..., description="Sorgulanacak otelin benzersiz kimliği")
    start_date: date = Field(..., description="Başlangıç tarihi")
    end_date: date = Field(..., description="Bitiş tarihi")
    room_type: Optional[str] = Field(None, description="Oda tipi filtresi (örn: Deluxe, Standart)")
    competitor_tracking: bool = Field(default=True, description="Rakip fiyat analizini dahil et")


# 2. Oda Bazlı Fiyat ve Doluluk Özeti DTO'su
class RoomPriceSummary(BaseModel):
    room_type: str = Field(..., description="Oda tipi")
    current_price_try: Decimal = Field(..., ge=0, description="Mevcut oda fiyatı (TRY)")
    recommended_price_try: Decimal = Field(..., ge=0, description="AI önerilen oda fiyatı (TRY)")
    occupancy_rate: float = Field(..., ge=0.0, le=100.0, description="Mevcut doluluk oranı (%)")
    currency: str = Field(default="TRY", description="Para birimi")


# 3. Kullanıcıya Dönen Birleşik Dashboard Yanıt DTO'su
class UserDashboardResponse(BaseModel):
    hotel_id: str = Field(..., description="Otel ID")
    hotel_name: Optional[str] = Field(None, description="Otel adı")
    
    # DB'den çekilen TL cinsinden birleşik fiyat ve genel metrikler
    average_current_price_try: Decimal = Field(..., ge=0, description="Ortalama mevcut fiyat (TRY)")
    recommended_price_try: Decimal = Field(..., ge=0, description="Genel tavsiye edilen fiyat (TRY)")
    currency: str = Field(default="TRY", description="Para birimi")
    
    overall_occupancy_rate: float = Field(..., ge=0.0, le=100.0, description="Toplam otel doluluk oranı (%)")
    #rooms: List[RoomPriceSummary] = Field(default_factory=list, description="Oda bazında kırılımlar")
    
    status: str = Field(default="OPTIMAL", description="Sistem durum özeti (örn: OPTIMAL, UNDERPRICED, OVERPRICED)")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Son veri güncellenme zamanı")

    # ORM veya DB modellerinden doğrudan parse edebilmek için
    model_config = ConfigDict(from_attributes=True)

# Cache miss anında DB'den (MongoDB/PostgreSQL) çekilen Read-Only kullanıcı & fiyat özeti
class UserReadSchema(BaseModel):
    user_id: str = Field(..., description="Kullanıcının tekil kimliği")
    hotel_id: Optional[str] = Field(None, description="Bağlı olduğu otel ID")
    tier: str = Field(default="FREE", description="Kullanıcı abonelik katmanı (FREE, PRO, ENTERPRISE)")
    is_active: bool = Field(default=True, description="Kullanıcı aktiflik durumu")
    
    # DB'den okunacak tavsiye edilen fiyat bilgisi (TRY)
    recommended_price_try: Optional[Decimal] = Field(None, ge=0, description="Tavsiye edilen güncel taban fiyat")
    
    created_at: datetime = Field(..., description="Hesap oluşturulma tarihi")

    # DB (ORM / ODM) nesnelerini veya MongoDB dict çıktılarını doğrudan parse etmek için
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
"""
Ortak Tipler ve Hata Yanıtları (Tüm Servisler)

    Modeller:

        StandardAPIResponse[T]: success: bool, data: Optional[T], error: Optional[ErrorDetail]

        SymbolEnum / CurrencyEnum: Desteklenen varlık sembolleri ve birimleri

        HealthCheckResponse: Servislerin /health ve /metrics meta bilgileri
"""
