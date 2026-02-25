class pwStruct:
    def __init__(self):
        self.pass_list = {}
        self.services = set()
        
    def serialize(self):
        return {
            "pass-list" : {
                service: login_list.serialize()
                for service, login_list in self.pass_list.items()
            }
            "services" : list(self.services)
        }

