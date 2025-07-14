from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, List

class User:
    """用户核心操作模型（所有方法均为静态方法）"""

    @staticmethod
    def _get_db():
        """获取数据库实例"""
        from ..core.database import get_db
        
        db = get_db()
        if db is None:
            raise RuntimeError("MongoDB connection not initialized")
        return db

    # === 账户基础功能 ===
    @staticmethod
    def create(username: str, email: str, password: str) -> Optional[str]:
        """创建新用户"""
        try:
            db = User._get_db()
                
            if db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
                return None

            user_id = db.users.insert_one({
                "username": username,
                "email": email,
                "password_hash": generate_password_hash(password),
                "balance": 0.00,  # 初始虚拟资金
                "favorite_stocks": [],  # 保留兼容性
                "is_active": True,      # 软删除标记
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }).inserted_id
            return str(user_id)
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None
    
    @staticmethod
    def verify_login(username: str, password: str) -> Optional[str]:
        """验证用户登录"""
        try:
            db = User._get_db()
            user = db.users.find_one({"username": username, "is_active": True})
            if user and check_password_hash(user["password_hash"], password):
                return str(user["_id"])
            return None
        except Exception as e:
            print(f"登录验证失败: {e}")
            return None

    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> bool:
        """修改密码（需验证旧密码）"""
        try:
            db = User._get_db()
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if not user or not check_password_hash(user["password_hash"], old_password):
                return False
            
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "password_hash": generate_password_hash(new_password),
                    "updated_at": datetime.utcnow()
                }}
            )
            return True
        except Exception as e:
            print(f"修改密码失败: {e}")
            return False

    # === 资料管理 ===
    @staticmethod
    def get_profile(user_id: str) -> Optional[Dict]:
        """获取用户公开资料"""
        try:
            db = User._get_db()
            user = db.users.find_one(
                {"_id": ObjectId(user_id), "is_active": True},
                {"password_hash": 0, "login_history": 0}  # 排除敏感字段
            )
            if not user:
                return None
            
            user["_id"] = str(user["_id"])  # 转换ObjectId为字符串
            return user
        except Exception as e:
            print(f"获取用户资料失败: {e}")
            return None

    @staticmethod
    def update_profile(user_id: str, **kwargs) -> bool:
        """更新用户资料"""
        try:
            db = User._get_db()
            allowed_fields = {"email", "avatar_url", "bio", "location"}
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if not updates:
                return False

            updates["updated_at"] = datetime.utcnow()
            result = db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"更新用户资料失败: {e}")
            return False

    # === 自选股管理 ===
    @staticmethod
    def add_favorite_stock(user_id: str, symbol: str) -> bool:
        """添加自选股"""
        try:
            db = User._get_db()
            
            # 检查是否已存在
            existing = db.user_favorites.find_one({
                "user_id": ObjectId(user_id),
                "symbol": symbol.upper()
            })
            
            if existing:
                return True  # 已存在，返回成功
            
            # 添加新的自选股
            favorite_data = {
                "user_id": ObjectId(user_id),
                "symbol": symbol.upper(),
                "added_at": datetime.utcnow()
            }
            
            result = db.user_favorites.insert_one(favorite_data)
            return bool(result.inserted_id)
            
        except Exception as e:
            print(f"添加自选股失败: {e}")
            return False

    @staticmethod
    def remove_favorite_stock(user_id: str, symbol: str) -> bool:
        """移除自选股"""
        try:
            db = User._get_db()
            result = db.user_favorites.delete_one({
                "user_id": ObjectId(user_id),
                "symbol": symbol.upper()
            })
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"移除自选股失败: {e}")
            return False

    @staticmethod
    def get_favorite_stocks(user_id: str) -> List[str]:
        """获取用户的自选股列表"""
        try:
            db = User._get_db()
            favorites = db.user_favorites.find({
                "user_id": ObjectId(user_id)
            }).sort("added_at", -1)
            
            return [fav["symbol"] for fav in favorites]
            
        except Exception as e:
            print(f"获取自选股失败: {e}")
            return []

    @staticmethod
    def is_favorite_stock(user_id: str, symbol: str) -> bool:
        """检查是否为自选股"""
        try:
            db = User._get_db()
            favorite = db.user_favorites.find_one({
                "user_id": ObjectId(user_id),
                "symbol": symbol.upper()
            })
            return favorite is not None
            
        except Exception as e:
            print(f"检查自选股状态失败: {e}")
            return False

    @staticmethod
    def get_favorite_stocks_with_details(user_id: str) -> List[Dict]:
        """获取用户的自选股详细信息"""
        try:
            db = User._get_db()
            from .stock import Stock
            
            # 获取用户自选股，包含添加时间
            favorites_cursor = db.user_favorites.find({
                "user_id": ObjectId(user_id)
            }).sort("added_at", -1)
            
            detailed_favorites = []
            
            for fav in favorites_cursor:
                symbol = fav["symbol"]
                added_at = fav["added_at"].isoformat()
                
                try:
                    # 获取股票基本信息
                    stock_data = Stock.get_stock_quote(symbol)
                    if stock_data:
                        detailed_favorites.append({
                            "symbol": symbol,
                            "price": stock_data.get("price", 0),
                            "change": stock_data.get("change", 0),
                            "change_percent": stock_data.get("change_percent", 0),
                            "volume": stock_data.get("volume", 0),
                            "added_at": added_at
                        })
                    else:
                        detailed_favorites.append({
                            "symbol": symbol,
                            "price": "N/A",
                            "change": "N/A", 
                            "change_percent": "N/A",
                            "volume": "N/A",
                            "added_at": added_at
                        })
                except Exception as e:
                    print(f"获取 {symbol} 详情失败: {e}")
                    detailed_favorites.append({
                        "symbol": symbol,
                        "price": "N/A",
                        "change": "N/A", 
                        "change_percent": "N/A",
                        "volume": "N/A",
                        "added_at": added_at
                    })
            print(f"处理后的自选股详情: {detailed_favorites}")  # 调试日志
            return detailed_favorites
            
        except Exception as e:
            print(f"获取自选股详情失败: {e}")
            return []
    
    # === 兼容性方法 ===
    @staticmethod
    def get_favorites(user_id: str) -> List[str]:
        """获取用户自选股列表（兼容旧版本）"""
        return User.get_favorite_stocks(user_id)

    @staticmethod
    def toggle_favorite(user_id: str, stock_symbol: str) -> bool:
        """添加/移除自选股"""
        try:
            if User.is_favorite_stock(user_id, stock_symbol):
                return User.remove_favorite_stock(user_id, stock_symbol)
            else:
                return User.add_favorite_stock(user_id, stock_symbol)
        except Exception as e:
            print(f"切换自选股失败: {e}")
            return False

    # === 账户安全 ===
    @staticmethod
    def record_login(user_id: str, ip_address: str) -> None:
        """记录用户登录历史"""
        try:
            db = User._get_db()
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {
                    "login_history": {
                        "ip": ip_address,
                        "timestamp": datetime.utcnow()
                    }
                }}
            )
        except Exception as e:
            print(f"记录登录历史失败: {e}")

    @staticmethod
    def deactivate(user_id: str) -> bool:
        """停用账户（软删除）"""
        try:
            db = User._get_db()
            result = db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"停用账户失败: {e}")
            return False