"""
PDF Generation Service
Uses Jinja2 templates + Playwright for HTML to PDF conversion
"""

import asyncio
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright


class PDFService:
    """Service for generating PDF reports."""
    
    _executor = ThreadPoolExecutor(max_workers=4)
    
    def __init__(self, user_id: Optional[UUID] = None):
        self.user_id = user_id
        
        # Templates directory
        base_dir = Path(__file__).parent.parent
        self.templates_dir = base_dir / "templates" / "pdf"
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
    )
    
    def _get_image_base64(self, image_name: str) -> str:
        """Convert local image to base64 data URL."""
        image_path = self.templates_dir / 'assets' / image_name
        if image_path.exists():
            with open(image_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
            ext = image_path.suffix.lower().strip('.')
            mime = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'gif': 'gif'}.get(ext, 'jpeg')
            return f"data:image/{mime};base64,{data}"
        return ""
    
    def _render_pdf_sync(self, template_name: str, context: Dict[str, Any]) -> bytes:
        """Render HTML template to PDF using Playwright (sync)."""
        template = self.env.get_template(template_name)
        html_content = template.render(**context)
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            page.set_content(html_content, wait_until='networkidle')
            
            pdf_bytes = page.pdf(
                format='A4',
                print_background=True,
                margin={'top': '0mm', 'right': '0mm', 'bottom': '0mm', 'left': '0mm'}
            )
            
            browser.close()
        
        return pdf_bytes
    
    async def _render_pdf(self, template_name: str, context: Dict[str, Any]) -> bytes:
        """Async wrapper - runs sync playwright in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._render_pdf_sync,
            template_name,
            context
        )
    
    # =========================================================================
    # CALCULATOR PDF GENERATORS
    # =========================================================================
    
    async def generate_gold_calculator_pdf(
        self,
        calculator_response: Dict[str, Any],
        client_name: str = "Valued Client",
        advisor_name: str = "Financial Advisor",
        products: Optional[List] = None,
    ) -> bytes:
        """Generate Gold Calculator PDF."""
        current_year = datetime.now().year
        years_to_goal = calculator_response.get('years_to_goal', 3)
        
        context = {
            'data': calculator_response,
            'client_name': client_name,
            'advisor_name': advisor_name,
            'report_date': datetime.now().strftime('%d/%m/%Y'),
            'target_year': current_year + years_to_goal,
            'products': products or [],
            'cover_image': self._get_image_base64('gold-cover.png'),
        }
        
        return await self._render_pdf('gold.html', context)
    
    # =========================================================================
    # EXISTING METHODS (stubs)
    # =========================================================================
    
    async def generate_goal_pdf(self, goal_id: UUID) -> str:
        raise NotImplementedError("Goal PDF not yet implemented")
    
    async def generate_mom_pdf(self, touchpoint_id: UUID) -> str:
        raise NotImplementedError("MoM PDF not yet implemented")
    
    async def generate_calculator_pdf(self, result_id: UUID) -> str:
        raise NotImplementedError("Calculator PDF not yet implemented")
    
    async def generate_client_report(self, client_id: UUID) -> str:
        raise NotImplementedError("Client report not yet implemented")