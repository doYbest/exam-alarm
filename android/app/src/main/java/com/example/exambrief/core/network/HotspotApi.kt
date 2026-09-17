package com.example.exambrief.core.network

import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Path
import retrofit2.http.Query

interface HotspotApi {
    @GET("v1/hotspots")
    suspend fun list(
        @Query("date") date: String,
        @Query("timezone") timezone: String,
        @Query("cursor") cursor: String? = null,
        @Header("If-None-Match") etag: String? = null,
    ): Response<ResponseBody>

    @GET("v1/hotspots/{id}")
    suspend fun detail(
        @Path("id") id: String,
        @Header("If-None-Match") etag: String? = null,
    ): Response<ResponseBody>
}
