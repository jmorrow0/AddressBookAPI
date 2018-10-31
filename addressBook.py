from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch
from flask_restful import Resource, Api
import re
import requests


es=Elasticsearch([{'host':'localhost','port':9200}])

app=Flask(__name__)
api=Api(app)
es.indices.create(index='index', ignore=400)

@app.route('/')
def test_service():
    response = requests.get('http://localhost:9200/')
    return response.content

def getClean(body, pageSize, page):
    response=es.search(index='index', doc_type='contact', body=body)
    nHits=int(response['hits']['total'])
    hits=[]
    for hit in response['hits']['hits']:
        hits.append(hit)
    onPages=page*pageSize
    if page==1:
        if pageSize>nHits:
            return jsonify(hits[:nHits])
        else:
            return jsonify(hits[:pageSize])
    elif nHits>onPages:
        return jsonify(hits[(page-1)*pageSize:onPages])
    else:
        if nHits>(page-1)*pageSize and nHits<onPage:
            return jsonify(hits[(page-1)*pageSize:nHits])
        else:
            return 'Error: requested page exceeds range of valid values', 400



class contacts(Resource):
    def get(self):
        if 'pageSize' in request.args:
            pageSize=int(request.args['pageSize'])
            if pageSize<1:
                return 'Error: page size must be a nonnegative, nonzero integer', 400
        else:
            pageSize=10

        if 'page' in request.args:
            page=int(request.args['page'])
            if page<1:
                return 'Error: page must be a nonnegative, nonzero integer', 400
        else:
            page=1

        if 'query' in request.args:
            searchTerm=request.args['query']
            body={
                'query':{
                    'query_string': {
                        'default_field': 'name',
                        'query': searchTerm
                    }
                }
            }
        else:
            body = {
                'query': {
                    'match_all': {

                    }
                }
            }
        return getClean(body, pageSize, page)


    def post(self):
        if not request.get_json().get('name'):
            return 'Error: name is a required field', 400
        name = request.get_json().get('name')

        if not request.get_json().get('phone'):
            return 'Error: phone is a required field', 400
        phone=request.get_json().get('phone')

        if not request.get_json().get('email'):
            return 'Error: email is a required field', 400
        email=request.get_json().get('email')

        if len(phone)>15:
            return 'Error: phone cannot exceed 15 digits', 400
        elif bool(re.match('[0-9]+$',phone))==False:
            return 'Error, phone can only contain digits', 400

        elif bool(re.match('[^@]+@[^@]+\.[^@]+',email)==False):
            return 'Error, email must be a valid email address',400

        else:  #No check for name validity - 'jamie', 'ke$ha', 'richard 3rd', and 'anne-marie' should all be valid names
            nameSearch={
                'query': {
                    'match': {
                        'name': name
                    }
                }
            }
            nameCheck=es.search(index='index', doc_type='contact', body=nameSearch)
            if nameCheck['hits']['total']!=0:
                return 'Error: contact already exists', 400
            index_body ={
                'name':name,
                'phone':phone,
                'email':email
            }
        return jsonify(es.index(index='index', refresh=True, doc_type='contact', body=index_body))



class contactsFilters(Resource):
    def findName(self, name):
        body = {
            'query': {
                'match': {
                    'name': name
                }
            }
        }
        found = es.search(index='index',doc_type='contact',body=body)
        if found['hits']['total']==0:
            return 'Error: contact not found', 404
        return found

    def get(self, name):
        return jsonify(self.findName(name))

    def put(self, name):
        retrieved=self.findName(name)
        ident=[]
        for entries in retrieved['hits']['hits']:
            ident.append(entries['_id'])
        # ident=retrieved['hits']['hits']['_id']
        phone=request.get_json().get('phone')
        email=request.get_json().get('email')
        if not phone:
            return 'Error: phone number field missing', 400
        if not email:
            return 'Error: email field missing', 400
        updated={
            'doc':{
                'name': name,
                'phone': phone,
                'email': email
            }
        }
        return jsonify(es.update(index='index', refresh=True, doc_type='contact', id=ident[0], body=updated))

    def delete(self, name):
        retrieved = self.findName(name)
        ident = []
        for entries in retrieved['hits']['hits']:
            ident.append(entries['_id'])
        # ident = retrieved['hits']['hits']['_id']
        return jsonify(es.delete(index='index', refresh=True, doc_type='contact', id=ident[0]))


api.add_resource(contacts, '/contacts')
api.add_resource(contactsFilters, '/contacts/<name>')



if __name__=='__main__':
    app.run(debug=True)