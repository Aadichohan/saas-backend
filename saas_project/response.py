from rest_framework.response import Response

# class DrfResponse():
#     def __init__(self, data=None, status=200, error=None, response = {}, headers=None):
#         self.data = data
#         self.status = status
#         self.error = error
#         self.response = response
#         self.headers = headers

#     def to_json(self):
#         if self.data:
#             response_data = {"data": self.data}
#         else: response_data = {}
#         if self.response:
#             response_data["response"] = self.response  
#         if self.error:
#             response_data["error"] = self.error  
#         return Response(response_data, status=self.status, headers=self.headers)

class DrfResponse():
    def __init__(self, data=None, status=200, error=None, response=None, headers=None):
        self.data = data
        self.status = status
        self.error = error or {} # Default empty dict
        self.response = response or {} # Default empty dict
        self.headers = headers

    def to_json(self):
        # Consistent Structure: Frontend ko hamesha pata hoga ke ye keys milengi
        response_payload = {
            "data": self.data if self.data is not None else [],
            "response": self.response,
            "error": self.error
        }
        
        return Response(response_payload, status=self.status, headers=self.headers)