import addressBook
import requests
import unittest
from unittest import TestCase
import json
from elasticsearch import Elasticsearch


class TestAddressBook(TestCase):
    def setUp(self):
        addressBook.app.testing = True
        self.app = addressBook.app.test_client()

    def tearDown(self):
        pass

    def test1_get_fail(self):
        response = self.app.get('/contacts/ajax', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test2_creation(self):
        response1 = self.create_contact('Alison', '122333', 'alison@aol.com')
        response2 = self.create_contact('Bony', '99933300', 'bony@gmail.com')
        response3 = self.create_contact('Alison', '123456', 'test@usa.gov')  # Duplication: should fail
        response4 = self.create_contact('Test', '122234', '55555') #invalid email, should fail
        response5 = self.create_contact('Henry', '1234567890123456', 'oopsallbones@hotmail.edu')  # Phone number > 15 digits: should fail
        response6 = self.create_contact('Devin','8883238843')  # No email provided: should fail
        response7 = self.create_contact('12345','ted@amazingadventure.org')  # No name provided: should fail
        response8 = self.create_contact('Devin', '1234aa','ted@amazingadventure.org')  # Phone number contains alphabets: should fail
        response9 = self.create_contact('ira','8478478844','dingbat@ssh.pi')
        self.assertEquals(response1.status_code, 200)
        self.assertEquals(response2.status_code, 200)
        self.assertEquals(response3.status_code, 400)
        self.assertEquals(response4.status_code, 400)
        self.assertEquals(response5.status_code, 400)
        self.assertEquals(response6.status_code, 400)
        self.assertEquals(response7.status_code, 400)
        self.assertEquals(response8.status_code, 400)
        self.assertEquals(response9.status_code, 200)

    def test3_get_all_contacts(self):
        response = self.app.get('/contacts', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test4_pagination(self):
        response1 = self.app.get('/contacts?pageSize=3&page=1', follow_redirects=True)
        response2 = self.app.get('/contacts?pageSize=3&page=2',
                                 follow_redirects=True)  # Only 3 contacts, so there should be no second page
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 400)

    def test5_queries(self):
        response1 = self.app.get('/contacts?pageSize=3&page=1&query=alison', follow_redirects=True)
        response2 = self.app.get('/contacts?pageSize=3&page=1&query=a*', follow_redirects=True)
        response3 = self.app.get('/contacts?pageSize=3&page=1&query=-alison', follow_redirects=True)
        response4 = self.app.get('/contacts?pageSize=3&page=1&query=alison+bony', follow_redirects=True)
        response5 = self.app.get('/contacts?pageSize=3&page=1&query=alison|bony', follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response4.status_code, 200)
        self.assertEqual(response5.status_code, 200)

    def test6_get_contact_by_name(self):
        response1 = self.app.get('/contacts/Alison', follow_redirects=True)
        response2 = self.app.get('/contacts/Bison', follow_redirects=True)  # No contact called Bison
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 400)

    def test7_edit_contact(self):
        response1 = self.edit_contact('Test', '3300033','jimbo@jimbo.jim')
        response2 = self.edit_contact('Alison')  # Cannot edit without providing the new phone number
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 400)

    def test8_deletion(self):
        response1 = self.app.delete('/contacts/Test', follow_redirects=True)
        response2 = self.app.delete('/contacts/Alison', follow_redirects=True)
        response3 = self.app.delete('/contacts/Bony', follow_redirects=True)
        response4 = self.app.delete('/contacts/Bubu', follow_redirects=True)  # No contact called Bubu
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response4.status_code, 400)

    # helpers
    def create_contact(self, name='', phone_number='', email=''):
        data = json.loads("{\n\t\"name\": \"" + name + "\",\n\t\"phone\": \"" + phone_number + "\",\n\t\"email\": \"" + email + "\"\n}")
        return requests.post('http://localhost:5000/contacts', json=data)

    def edit_contact(self, name, phone_number='', email=''):
        data = json.loads("{\n\t\"phone_number\": \"" + phone_number + "\"\n}")
        return requests.put('http://localhost:5000/contacts/' + name, json=data)


if __name__ == '__main__':
    unittest.main()