from uuid import UUID
from typing import Optional, List
from datetime import date, datetime
from app.database import supabase
from app.models.product import ProductResponse, ProductListResponse, ProductSearchParams
from app.models.client_product import (
    ClientProductCreate, ClientProductUpdate, ClientProductResponse,
    ClientProductListResponse, ClientPortfolioSummary, UpdateValueRequest,
    BulkUpdateValueRequest, BulkUpdateValueResponse
)
from app.models.product_transaction import (
    ProductTransactionCreate, ProductTransactionResponse, 
    ProductTransactionListResponse, TransactionSummary
)


class ClientProductService:
    """Service for managing client products and transactions"""
    
    def __init__(self, user_id: UUID):
        self.user_id = user_id
    
    # ==================== MASTER PRODUCTS ====================
    
    async def list_master_products(
        self, 
        category: Optional[str] = None,
        provider_name: Optional[str] = None,
        fund_type: Optional[str] = None,
        supports_sip: Optional[bool] = None,
        search: Optional[str] = None
    ) -> ProductListResponse:
        """Get master list of available products"""
        query = supabase.table("products").select("*").eq("is_active", True)
        
        # Apply filters
        if category:
            query = query.eq("category", category)
        if provider_name:
            query = query.eq("provider_name", provider_name)
        if fund_type:
            query = query.eq("fund_type", fund_type)
        if supports_sip is not None:
            query = query.eq("supports_sip", supports_sip)
        if search:
            query = query.ilike("name", f"%{search}%")
        
        response = query.execute()
        
        products = [ProductResponse(**product) for product in response.data]
        
        return ProductListResponse(
            products=products,
            total=len(products)
        )
    
    async def get_master_product(self, product_id: UUID) -> Optional[ProductResponse]:
        """Get single product by id"""
        response = supabase.table("products").select("*").eq("id", str(product_id)).execute()
        
        if not response.data:
            return None
        
        return ProductResponse(**response.data[0])
    
    # ==================== CLIENT PRODUCTS ====================
    
    async def get_client_products(
        self,
        client_id: UUID,
        category: Optional[str] = None,
        status: str = "active",
        investment_type: Optional[str] = None
    ) -> ClientProductListResponse:
        """Get all products for a client"""
        query = (
            supabase.table("client_products")
            .select("*, goals(name)")
            .eq("user_id", str(self.user_id))
            .eq("client_id", str(client_id))
        )
        
        # Apply filters
        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)
        if investment_type:
            query = query.eq("investment_type", investment_type)
        
        response = query.execute()
        
        # Calculate totals
        total_invested = 0
        total_current_value = 0
        total_sip = 0
        
        products = []
        for product_data in response.data:
            # Extract goal_name if exists
            goal_name = product_data.get("goals", {}).get("name") if product_data.get("goals") else None
            
            # Calculate gain/loss
            invested = product_data.get("invested_amount", 0)
            current = product_data.get("current_value", 0)
            gain_loss, gain_loss_percent = self._calculate_gain_loss(invested, current)
            
            # Add calculated fields
            product_data["goal_name"] = goal_name
            product_data["gain_loss"] = gain_loss
            product_data["gain_loss_percent"] = gain_loss_percent
            
            # Update totals
            total_invested += invested
            total_current_value += current
            total_sip += product_data.get("sip_amount", 0)
            
            products.append(ClientProductResponse(**product_data))
        
        total_gain_loss = total_current_value - total_invested
        
        return ClientProductListResponse(
            products=products,
            total=len(products),
            total_invested=total_invested,
            total_current_value=total_current_value,
            total_gain_loss=total_gain_loss,
            total_sip=total_sip
        )
    
    async def add_client_product(self, data: ClientProductCreate) -> ClientProductResponse:
        """Add a product to client's portfolio"""
        # Validate client belongs to user
        client_check = (
            supabase.table("clients")
            .select("id")
            .eq("id", str(data.client_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        
        if not client_check.data:
            raise ValueError("Client not found or does not belong to user")
        
        # If product_id provided, validate it exists
        if data.product_id:
            product_check = (
                supabase.table("products")
                .select("id")
                .eq("id", str(data.product_id))
                .execute()
            )
            if not product_check.data:
                raise ValueError("Master product not found")
        
        # Prepare insert data — mode="json" converts date/enum/UUID to strings
        insert_data = data.model_dump(mode="json", exclude_unset=True)
        insert_data["user_id"] = str(self.user_id)
        insert_data["status"] = "active"  # Default status

        response = supabase.table("client_products").insert(insert_data).execute()
        
        if not response.data:
            raise ValueError("Failed to create client product")
        
        # Get the created product with calculated fields
        return await self.get_client_product(UUID(response.data[0]["id"]))
    
    async def get_client_product(self, product_id: UUID) -> Optional[ClientProductResponse]:
        """Get single client product by id"""
        response = (
            supabase.table("client_products")
            .select("*, goals(name)")
            .eq("id", str(product_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        
        if not response.data:
            return None
        
        product_data = response.data[0]
        
        # Extract goal_name if exists
        goal_name = product_data.get("goals", {}).get("name") if product_data.get("goals") else None
        
        # Calculate gain/loss
        invested = product_data.get("invested_amount", 0)
        current = product_data.get("current_value", 0)
        gain_loss, gain_loss_percent = self._calculate_gain_loss(invested, current)
        
        # Add calculated fields
        product_data["goal_name"] = goal_name
        product_data["gain_loss"] = gain_loss
        product_data["gain_loss_percent"] = gain_loss_percent
        
        return ClientProductResponse(**product_data)
    
    async def update_client_product(self, product_id: UUID, data: ClientProductUpdate) -> ClientProductResponse:
        """Update a client product"""
        # Validate product belongs to user
        existing = await self.get_client_product(product_id)
        if not existing:
            raise ValueError("Product not found or does not belong to user")
        
        # Prepare update data — mode="json" converts date/enum/UUID to strings
        update_data = data.model_dump(mode="json", exclude_unset=True)

        # If current_value changed, set last_updated_date
        if "current_value" in update_data:
            update_data["last_updated_date"] = date.today().isoformat()
        
        response = (
            supabase.table("client_products")
            .update(update_data)
            .eq("id", str(product_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        
        if not response.data:
            raise ValueError("Failed to update product")
        
        return await self.get_client_product(product_id)
    
    async def update_product_value(self, product_id: UUID, data: UpdateValueRequest) -> ClientProductResponse:
        """Quick update for current value/NAV"""
        # Validate product belongs to user
        existing = await self.get_client_product(product_id)
        if not existing:
            raise ValueError("Product not found or does not belong to user")
        
        update_data = {
            "current_value": data.current_value,
            "last_updated_date": (data.last_updated_date or date.today()).isoformat()
        }
        
        if data.nav is not None:
            update_data["nav"] = data.nav
        if data.units is not None:
            update_data["units"] = data.units
        
        response = (
            supabase.table("client_products")
            .update(update_data)
            .eq("id", str(product_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        
        if not response.data:
            raise ValueError("Failed to update product value")
        
        return await self.get_client_product(product_id)
    
    async def delete_client_product(self, product_id: UUID) -> dict:
        """Delete a client product"""
        # Validate product belongs to user
        existing = await self.get_client_product(product_id)
        if not existing:
            raise ValueError("Product not found or does not belong to user")
        
        response = (
            supabase.table("client_products")
            .delete()
            .eq("id", str(product_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        
        return {"message": "Product deleted successfully"}
    
    async def get_portfolio_summary(self, client_id: UUID) -> ClientPortfolioSummary:
        """Get portfolio summary with category breakdown"""
        # Get client name
        client_response = (
            supabase.table("clients")
            .select("name")
            .eq("id", str(client_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        
        if not client_response.data:
            raise ValueError("Client not found")
        
        client_name = client_response.data[0]["name"]
        
        # Get all active products
        products_response = (
            supabase.table("client_products")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("client_id", str(client_id))
            .eq("status", "active")
            .execute()
        )
        
        # Calculate totals and groupings
        total_invested = 0
        total_current_value = 0
        total_sip = 0
        by_category = {}
        by_investment_type = {}
        by_provider = {}
        products_count = len(products_response.data)
        active_sips_count = 0
        
        for product in products_response.data:
            invested = product.get("invested_amount", 0)
            current = product.get("current_value", 0)
            sip = product.get("sip_amount", 0)
            category = product.get("category", "other")
            investment_type = product.get("investment_type", "lumpsum")
            provider = product.get("provider_name", "Unknown")
            
            total_invested += invested
            total_current_value += current
            total_sip += sip
            
            if sip > 0:
                active_sips_count += 1
            
            # Group by category
            by_category[category] = by_category.get(category, 0) + current
            
            # Group by investment type
            by_investment_type[investment_type] = by_investment_type.get(investment_type, 0) + current
            
            # Group by provider
            if provider:
                by_provider[provider] = by_provider.get(provider, 0) + current
        
        total_gain_loss = total_current_value - total_invested
        total_gain_loss_percent = (
            (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
        )
        
        return ClientPortfolioSummary(
            client_id=client_id,
            client_name=client_name,
            total_aum=total_current_value,
            total_invested=total_invested,
            total_current_value=total_current_value,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=total_gain_loss_percent,
            total_sip=total_sip,
            by_category=by_category,
            by_investment_type=by_investment_type,
            by_provider=by_provider,
            products_count=products_count,
            active_sips_count=active_sips_count
        )
    
    async def bulk_update_values(self, data: BulkUpdateValueRequest) -> BulkUpdateValueResponse:
        """Update multiple product values at once"""
        updated_count = 0
        failed_count = 0
        errors = []
        
        for item in data.updates:
            try:
                # Validate product belongs to user
                existing = await self.get_client_product(item.product_id)
                if not existing:
                    failed_count += 1
                    errors.append({
                        "product_id": str(item.product_id),
                        "error": "Product not found"
                    })
                    continue
                
                update_data = {
                    "current_value": item.current_value,
                    "last_updated_date": date.today().isoformat()
                }
                
                if item.nav is not None:
                    update_data["nav"] = item.nav
                if item.units is not None:
                    update_data["units"] = item.units
                
                response = (
                    supabase.table("client_products")
                    .update(update_data)
                    .eq("id", str(item.product_id))
                    .eq("user_id", str(self.user_id))
                    .execute()
                )
                
                if response.data:
                    updated_count += 1
                else:
                    failed_count += 1
                    errors.append({
                        "product_id": str(item.product_id),
                        "error": "Update failed"
                    })
            
            except Exception as e:
                failed_count += 1
                errors.append({
                    "product_id": str(item.product_id),
                    "error": str(e)
                })
        
        return BulkUpdateValueResponse(
            updated_count=updated_count,
            failed_count=failed_count,
            errors=errors
        )
    
    # ==================== TRANSACTIONS ====================
    
    async def add_transaction(self, data: ProductTransactionCreate) -> ProductTransactionResponse:
        """Add a product transaction"""
        # Validate client_product belongs to user
        product = await self.get_client_product(data.client_product_id)
        if not product:
            raise ValueError("Product not found or does not belong to user")
        
        # Prepare insert data — mode="json" converts date/enum/UUID to strings
        insert_data = data.model_dump(mode="json", exclude_unset=True)
        insert_data["user_id"] = str(self.user_id)
        
        # Insert transaction
        response = supabase.table("product_transactions").insert(insert_data).execute()
        
        if not response.data:
            raise ValueError("Failed to create transaction")
        
        transaction = response.data[0]
        
        # Update client_product based on transaction type
        update_data = {}
        
        if data.transaction_type in ["sip_installment", "additional_purchase", "lumpsum"]:
            # Increase invested amount
            new_invested = product.invested_amount + data.amount
            update_data["invested_amount"] = new_invested
            
            if data.units is not None:
                update_data["units"] = (product.units or 0) + data.units
            if data.nav is not None:
                update_data["nav"] = data.nav
        
        elif data.transaction_type in ["redemption", "partial_redemption"]:
            # Decrease current value
            new_current = max(0, product.current_value - data.amount)
            update_data["current_value"] = new_current
            
            if data.units is not None:
                update_data["units"] = max(0, (product.units or 0) - data.units)
        
        # Apply updates if any
        if update_data:
            supabase.table("client_products").update(update_data).eq("id", str(data.client_product_id)).execute()
        
        return ProductTransactionResponse(**transaction)
    
    async def get_transactions(
        self, 
        client_product_id: UUID,
        transaction_type: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> ProductTransactionListResponse:
        """Get transactions for a client product"""
        # Validate client_product belongs to user
        product = await self.get_client_product(client_product_id)
        if not product:
            raise ValueError("Product not found or does not belong to user")
        
        query = (
            supabase.table("product_transactions")
            .select("*")
            .eq("client_product_id", str(client_product_id))
            .eq("user_id", str(self.user_id))
            .order("transaction_date", desc=True)
        )
        
        # Apply filters
        if transaction_type:
            query = query.eq("transaction_type", transaction_type)
        if date_from:
            query = query.gte("transaction_date", date_from.isoformat())
        if date_to:
            query = query.lte("transaction_date", date_to.isoformat())
        
        response = query.execute()
        
        # Calculate totals
        total_invested = 0
        total_redeemed = 0
        
        purchase_types = ["sip_installment", "additional_purchase", "lumpsum"]
        redemption_types = ["redemption", "partial_redemption"]
        
        transactions = []
        for txn_data in response.data:
            transactions.append(ProductTransactionResponse(**txn_data))
            
            txn_type = txn_data.get("transaction_type")
            amount = txn_data.get("amount", 0)
            
            if txn_type in purchase_types:
                total_invested += amount
            elif txn_type in redemption_types:
                total_redeemed += amount
        
        net_investment = total_invested - total_redeemed
        
        return ProductTransactionListResponse(
            transactions=transactions,
            total=len(transactions),
            total_invested=total_invested,
            total_redeemed=total_redeemed,
            net_investment=net_investment
        )
    
    async def get_transaction_summary(self, client_product_id: UUID) -> TransactionSummary:
        """Get transaction summary for a client product"""
        # Validate client_product belongs to user
        product = await self.get_client_product(client_product_id)
        if not product:
            raise ValueError("Product not found or does not belong to user")
        
        # Get all transactions
        response = (
            supabase.table("product_transactions")
            .select("*")
            .eq("client_product_id", str(client_product_id))
            .eq("user_id", str(self.user_id))
            .order("transaction_date", desc=False)
            .execute()
        )
        
        if not response.data:
            raise ValueError("No transactions found")
        
        # Calculate summary
        total_invested = 0
        total_redeemed = 0
        sip_installments_count = 0
        
        purchase_types = ["sip_installment", "additional_purchase", "lumpsum"]
        redemption_types = ["redemption", "partial_redemption"]
        
        for txn in response.data:
            txn_type = txn.get("transaction_type")
            amount = txn.get("amount", 0)
            
            if txn_type in purchase_types:
                total_invested += amount
            elif txn_type in redemption_types:
                total_redeemed += amount
            
            if txn_type == "sip_installment":
                sip_installments_count += 1
        
        first_transaction = response.data[0]
        last_transaction = response.data[-1]
        
        return TransactionSummary(
            client_product_id=client_product_id,
            product_name=product.product_name,
            total_transactions=len(response.data),
            first_transaction_date=datetime.fromisoformat(first_transaction["transaction_date"]).date(),
            last_transaction_date=datetime.fromisoformat(last_transaction["transaction_date"]).date(),
            total_invested=total_invested,
            total_redeemed=total_redeemed,
            sip_installments_count=sip_installments_count
        )
    
    # ==================== HELPERS ====================
    
    def _calculate_gain_loss(self, invested: float, current: float) -> tuple:
        """Calculate gain/loss and percentage"""
        gain_loss = current - invested
        gain_loss_percent = ((current - invested) / invested * 100) if invested > 0 else 0
        return (gain_loss, gain_loss_percent)
