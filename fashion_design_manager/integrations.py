"""Swappable mock and REST integration clients."""
import os
import requests

class MockTrelloClient:
    def get_boards(self): return [{"id":"demo-board","name":"Spring 2027 Collection"}]
    def get_lists(self,board_id): return [{"id":"demo-list","name":"Production"}]
    def get_cards(self): return [{"id":"demo-card","name":"Production: Spring 2027 · Eco Denim Jacket","list":"Production"}]
    def create_card(self,name,description="",list_id="demo-list",due=None): return {"id":"DEMO-"+str(abs(hash(name))%99999),"name":name,"url":"https://trello.com/demo"}
    def update_card(self,card_id,**fields): return {"id":card_id,**fields}

class RealTrelloClient:
    def __init__(self,key=None,token=None): self.key=key or os.getenv("TRELLO_API_KEY"); self.token=token or os.getenv("TRELLO_TOKEN")
    def _get(self,path,**params):
        r=requests.get("https://api.trello.com/1/"+path,params={**params,"key":self.key,"token":self.token},timeout=15); r.raise_for_status(); return r.json()
    def get_boards(self): return self._get("members/me/boards",fields="name")
    def get_lists(self,board_id): return self._get(f"boards/{board_id}/lists",fields="name")
    def get_cards(self): return self._get("members/me/cards",fields="name,idList,due,url")
    def create_card(self,name,description="",list_id="",due=None):
        r=requests.post("https://api.trello.com/1/cards",params={"key":self.key,"token":self.token,"idList":list_id,"name":name,"desc":description,"due":due},timeout=15); r.raise_for_status(); return r.json()
    def update_card(self,card_id,**fields):
        r=requests.put(f"https://api.trello.com/1/cards/{card_id}",params={"key":self.key,"token":self.token,**fields},timeout=15); r.raise_for_status(); return r.json()

class MockShopifyClient:
    def create_product(self,product): return {"id":"DEMO-"+str(abs(hash(product.get("title","")))%99999),"title":product.get("title"),"status":"draft"}
    def update_product(self,product_id,product): return {"id":product_id,**product}
    def get_products(self): return []
    def update_inventory(self,*args,**kwargs): return {"status":"updated","demo":True}

class RealShopifyClient:
    def __init__(self,store=None,token=None): self.store=(store or os.getenv("SHOPIFY_STORE_URL","")).replace("https://","").strip("/"); self.token=token or os.getenv("SHOPIFY_ACCESS_TOKEN")
    def _request(self,method,path,**kwargs):
        if not self.store or not self.token: raise ValueError("Set Shopify store URL and access token in .env first.")
        r=requests.request(method,f"https://{self.store}/admin/api/2025-01/{path}",headers={"X-Shopify-Access-Token":self.token},timeout=20,**kwargs); r.raise_for_status(); return r.json()
    def create_product(self,product): return self._request("POST","products.json",json={"product":product})["product"]
    def update_product(self,product_id,product): return self._request("PUT",f"products/{product_id}.json",json={"product":product})["product"]
    def get_products(self): return self._request("GET","products.json").get("products",[])
    def update_inventory(self,*args,**kwargs): raise NotImplementedError("Configure a Shopify inventory location and item mapping to update inventory.")

class IllustratorClient:
    """Exports editable SVG and PNG assets; does not automate Adobe Illustrator."""
    @staticmethod
    def export_svg(name,category,color,path):
        from html import escape
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="900" viewBox="0 0 800 900"><rect width="800" height="900" fill="#f5f1e9"/><text x="60" y="110" font-family="sans-serif" font-size="24" fill="#59645b">ATELIER / DESIGN STUDY</text><path d="M300 210 L220 260 L160 440 L245 475 L285 365 L270 690 L530 690 L515 365 L555 475 L640 440 L580 260 L500 210 Q400 255 300 210Z" fill="{escape(color or "#8d9b84")}" stroke="#35433b" stroke-width="8"/><text x="60" y="790" font-family="serif" font-size="40" fill="#26352e">{escape(name)}</text><text x="60" y="835" font-family="sans-serif" font-size="22" fill="#59645b">{escape(category)} · editable vector concept</text></svg>'
        from pathlib import Path
        Path(path).write_text(svg,encoding="utf-8"); return path
