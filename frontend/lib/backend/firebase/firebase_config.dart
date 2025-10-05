import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';

Future initFirebase() async {
  if (kIsWeb) {
    await Firebase.initializeApp(
        options: FirebaseOptions(
            apiKey: "AIzaSyBUKvqd5amYhpQF5lMrEmmyuJEwxZXYnFc",
            authDomain: "hack-r-u25-yx6luc.firebaseapp.com",
            projectId: "hack-r-u25-yx6luc",
            storageBucket: "hack-r-u25-yx6luc.firebasestorage.app",
            messagingSenderId: "840409825557",
            appId: "1:840409825557:web:18dc29c04d8da5bf86e91c",
            measurementId: "G-RLBTMH1LH6"));
  } else {
    await Firebase.initializeApp();
  }
}
