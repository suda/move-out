import os
from PIL import Image

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from .models import Thing, Taker
from .utils import resize_image, WIDTH, HEIGHT


class ThingBasicTest(TestCase):
    def setUp(self):
        self.book = Thing.objects.create(name='Book')
        self.table = Thing.objects.create(name='Table')
        self.ola = Taker.objects.create(
            name='Ola',
        )
        self.tomek = Taker.objects.create(
            name='Tomek',
        )


class ThingTest(ThingBasicTest):
    def test_things_are_displayed(self):
        url = reverse('things:list', kwargs={'token': self.ola.token})
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'things/list.html')
        self.assertContains(response, self.book.name)
        self.assertContains(response, self.table.name)

    def test_thing_detail_page_is_displayed(self):
        url = reverse('things:detail',
                      kwargs={'pk': self.book.pk, 'token': self.ola.token})
        response = self.client.get(url)

        self.assertTemplateUsed(response, 'things/detail.html')
        self.assertContains(response, self.book.name)

    def test_thing_taken_by_user(self):
        self.book.taken_by = self.ola
        self.book.save()
        url = reverse('things:detail',
                      kwargs={'pk': self.book.pk, 'token': self.ola.token})
        response = self.client.get(url)
        self.assertContains(response, self.book.taken_by.name)


class TakeThingTest(ThingBasicTest):
    def test_take_thing(self):
        url = reverse('things:take',
                      kwargs={'pk': self.book.pk, 'token': self.ola.token})
        response = self.client.post(url, data={'taker_token': self.ola.token})
        self.assertRedirects(response, reverse(
            'things:detail',
            kwargs={'token': self.ola.token, 'pk': self.book.pk}))
        book = Thing.objects.get(pk=self.book.pk)
        self.assertEquals(self.ola, book.taken_by)

    def test_take_thing_with_invalid_token(self):
        invalid_token = '25648235'
        url = reverse('things:take',
                      kwargs={'pk': self.book.pk, 'token': invalid_token})
        response = self.client.post(url, data={})
        self.assertEquals(404, response.status_code)

    def test_token_from_url_in_take_form(self):
        url = reverse('things:detail',
                      kwargs={'pk': self.book.pk, 'token': self.ola.token})
        response = self.client.get(url)

        self.assertTemplateUsed(response, 'things/detail.html')
        self.assertContains(response, self.ola.token)

    def test_no_form_displayed_when_thing_taken(self):
        self.book.taken_by = self.tomek
        self.book.save()
        url = reverse('things:detail',
                      kwargs={'pk': self.book.pk, 'token': self.ola.token})
        response = self.client.get(url)
        self.assertNotContains(response, '<form')

    def test_cannot_take_thing_when_its_taken(self):
        self.book.taken_by = self.tomek
        self.book.save()
        url = reverse('things:take', kwargs={'token': self.ola.token,
                                             'pk': self.book.pk})
        response = self.client.post(url, data={'taker_token': self.ola.token})
        self.assertEqual(404, response.status_code)


class GiveBackThingTest(ThingBasicTest):
    def test_give_back_thing(self):
        self.book.taken_by = self.ola
        self.book.save()
        url = reverse('things:give_back',
                      kwargs={'pk': self.book.pk, 'token': self.ola.token})
        response = self.client.post(url, data={'taker_token': self.ola.token})

        self.assertEqual(302, response.status_code)
        book = Thing.objects.get(pk=self.book.pk)
        self.assertEquals(None, book.taken_by)

    def test_no_give_back_form_when_taken_by_others(self):
        self.book.taken_by = self.tomek
        self.book.save()
        url = reverse('things:detail',
                      kwargs={'pk': self.book.pk, 'token': self.ola.token})
        response = self.client.get(url)
        self.assertNotContains(response, '<form')

    def test_cannot_give_back_thing_taken_by_others(self):
        self.book.taken_by = self.tomek
        self.book.save()
        url = reverse('things:give_back', kwargs={'token': self.ola.token,
                                                  'pk': self.book.pk})
        response = self.client.post(url, data={'taker_token': self.ola.token})
        self.assertEqual(404, response.status_code)


class ThingModelTest(ThingBasicTest):
    def test_give_to(self):
        self.assertEqual(None, self.book.taken_by)
        self.book.give_to(self.ola)
        book = Thing.objects.get(pk=self.book.pk)
        self.assertEqual(self.ola, book.taken_by)

    def test_cannot_give_the_same_thing_twice(self):
        self.book.taken_by = self.tomek
        self.book.save()
        with self.assertRaises(ValueError):
            self.book.give_to(self.ola)

    def test_give_back(self):
        self.book.taken_by = self.ola
        self.book.save()
        self.book.give_back(self.ola)
        book = Thing.objects.get(pk=self.book.pk)
        self.assertEqual(None, book.taken_by)

    def test_cannot_give_back_for_other_user(self):
        self.book.taken_by = self.tomek
        self.book.save()
        self.book.give_back(self.ola)
        book = Thing.objects.get(pk=self.book.pk)
        self.assertEqual(self.tomek, book.taken_by)


class ThingAddFormTest(ThingBasicTest):
    def setUp(self):
        super(ThingAddFormTest, self).setUp()
        self.user = User.objects.create_superuser('user', 'test@test.com',
            'pass')
        self.client.login(username='user', password='pass')

    def test_add(self):
        url = reverse('things:add', kwargs={'token': self.ola.token})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'things/add.html')
        self.assertIn('form', response.context)


class ResizeImageTest(TestCase):
    def test_resize_image(self):
        picture_file = resize_image(open(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'test_img.png')))
        image = Image.open(picture_file)
        self.assertTrue(image.size[0] <= WIDTH)
        self.assertTrue(image.size[1] <= HEIGHT)
