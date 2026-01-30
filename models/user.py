class User:
    def __init__(self, id, nome, email, senha):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha
    
    def to_dict(self, include_senha=False):
        data = {
            "id": self.id,
            "nome": self.nome,
            "email": self.email
        }

        if include_senha:
            data["senha"] = self.senha
        
        return data