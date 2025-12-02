from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),

    # Student

    path('upload/', views.upload_students, name='upload_students'),
    path('add/', views.add_student_manual, name='add_student_manual'),
    path('reset/', views.reset_students_db, name='reset_students_db'),


    # Room
    path('rooms/add/', views.add_room, name='add_room'),
    path('rooms/delete/<int:room_id>/', views.delete_room, name='delete_room'),

   path('view-allotments/', views.view_allotments, name='view_allotments'),
    path('view-allotments/<str:room_no>/', views.view_room_allocation, name='view_room_allocation'),
    path('generate-seats/', views.generate_seats_view, name='generate_seats'),
    
    path('view-allotments/', views.view_allotments, name='view_allotments'),
    path('view-allotments/<str:room_no>/', views.view_room_allocation, name='view_room_allocation'),
    path('generate-seats/', views.generate_seats_view, name='generate_seats'),
 

      path('generate-seats/', views.generate_seats, name='generate_seats'),
  path('view_allotments/', views.view_allotments, name='view_allotments'),
  path('export_pdf/', views.export_pdf, name='export_pdf'),
  path('export_pdf/', views.export_pdf, name='export_pdf'),



      ]
