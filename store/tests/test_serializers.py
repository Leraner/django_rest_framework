from django.contrib.auth.models import User
from django.db.models import Case, Count, When, Avg, F
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1', first_name='Ivan', last_name='Petrov')
        self.user2 = User.objects.create(username='user2', first_name='Ivan', last_name='Sidorov')
        self.user3 = User.objects.create(username='user3', first_name='1', last_name='2')
        self.book_1 = Book.objects.create(name='TestBook_1', price=100,
                                          author_name='Author 1', owner=self.user1)
        self.book_2 = Book.objects.create(name='TestBook_2', price=125,
                                          author_name='Author 2', discount=30)

    def test_ok(self):
        UserBookRelation.objects.create(user=self.user1, book=self.book_1, like=True,
                                        rate=5)
        UserBookRelation.objects.create(user=self.user2, book=self.book_1, like=True,
                                        rate=5)
        UserBookRelation.objects.create(user=self.user3, book=self.book_1, like=True,
                                        rate=4)

        UserBookRelation.objects.create(user=self.user1, book=self.book_2, like=True,
                                        rate=3)
        UserBookRelation.objects.create(user=self.user2, book=self.book_2, like=True,
                                        rate=4)
        UserBookRelation.objects.create(user=self.user3, book=self.book_2, like=False)

        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rate'),
            annotated_discount_price=F('price') - F('discount')
        ).order_by('id')

        data = BooksSerializer(books, many=True).data
        expected_data = [
            {
                'id': self.book_1.id,
                'name': 'TestBook_1',
                'price': '100.00',  # Две точки после запятой, потому что в модели DecimalField
                'author_name': 'Author 1',
                'annotated_likes': 3,
                'annotated_discount_price': None,
                'rating': '4.67',
                'owner_name': 'user1',
                'readers': [
                    {
                        'first_name': 'Ivan',
                        'last_name': 'Petrov'
                    },
                    {
                        'first_name': 'Ivan',
                        'last_name': 'Sidorov'
                    },
                    {
                        'first_name': '1',
                        'last_name': '2'
                    },
                ]
            },
            {
                'id': self.book_2.id,
                'name': 'TestBook_2',
                'price': '125.00',
                'author_name': 'Author 2',
                'annotated_likes': 2,
                'annotated_discount_price': '95.00',
                'rating': '3.50',
                'owner_name': '',
                'readers': [
                    {
                        'first_name': 'Ivan',
                        'last_name': 'Petrov'
                    },
                    {
                        'first_name': 'Ivan',
                        'last_name': 'Sidorov'
                    },
                    {
                        'first_name': '1',
                        'last_name': '2'
                    },
                ]
        }
        ]
        print(expected_data)
        print(data)
        self.assertEqual(expected_data, data)
