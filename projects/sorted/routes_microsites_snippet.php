<?php

use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Microsite Routes (Static HTML Fallbacks)
|--------------------------------------------------------------------------
| Ensures that even if Nginx falls back to Laravel, the static microsite
| directories under public/ are correctly routed or served directly.
*/

Route::get('/ai-audit', function () {
    return response()->file(public_path('ai-audit/index.html'));
});

Route::get('/career', function () {
    return response()->file(public_path('career/index.html'));
});

Route::get('/consult', function () {
    return response()->file(public_path('consult/index.html'));
});

Route::get('/rota', function () {
    return response()->file(public_path('rota/index.html'));
});
