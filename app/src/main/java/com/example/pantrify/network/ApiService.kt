package com.example.pantrify.network

import com.example.pantrify.model.*
import retrofit2.http.*

interface ApiService {
    @POST("api/auth/login") suspend fun login(@Body body: LoginRequest): ApiResponse<AuthData>
    @POST("api/auth/register") suspend fun register(@Body body: RegisterRequest): ApiResponse<AuthData>
    @POST("api/auth/refresh") suspend fun refresh(@Body body: RefreshRequest): ApiResponse<AuthData>
    @POST("api/auth/logout") suspend fun logout(@Body body: RefreshRequest): retrofit2.Response<Unit>
    @GET("api/auth/me") suspend fun me(): ApiResponse<User>
    @GET("api/categories") suspend fun categories(@Query("search") search: String? = null): ApiResponse<List<Category>>
    @POST("api/categories") suspend fun createCategory(@Body body: CategoryRequest): ApiResponse<Category>
    @PUT("api/categories/{id}") suspend fun updateCategory(@Path("id") id: Int, @Body body: CategoryRequest): ApiResponse<Category>
    @DELETE("api/categories/{id}") suspend fun deleteCategory(@Path("id") id: Int): retrofit2.Response<Unit>
    @GET("api/products") suspend fun products(@Query("search") search: String? = null): ApiResponse<List<Product>>
    @POST("api/products") suspend fun createProduct(@Body body: ProductRequest): ApiResponse<Product>
    @PUT("api/products/{id}") suspend fun updateProduct(@Path("id") id: Int, @Body body: ProductRequest): ApiResponse<Product>
    @DELETE("api/products/{id}") suspend fun deleteProduct(@Path("id") id: Int): retrofit2.Response<Unit>
    @GET("api/inventory") suspend fun inventory(@Query("search") search: String? = null): ApiResponse<List<Inventory>>
    @POST("api/inventory") suspend fun createInventory(@Body body: InventoryRequest): ApiResponse<Inventory>
    @PUT("api/inventory/{id}") suspend fun updateInventory(@Path("id") id: Int, @Body body: InventoryRequest): ApiResponse<Inventory>
    @DELETE("api/inventory/{id}") suspend fun deleteInventory(@Path("id") id: Int): retrofit2.Response<Unit>
    @POST("api/inventory/consume/{productId}") suspend fun consume(@Path("productId") productId: Int, @Query("quantity") quantity: Double): ApiResponse<List<Inventory>>
    @GET("api/users") suspend fun users(@Query("search") search: String? = null): ApiResponse<List<User>>
    @PUT("api/users/{id}") suspend fun updateUser(@Path("id") id: Int, @Body body: UserUpdate): ApiResponse<User>
    @DELETE("api/users/{id}") suspend fun deleteUser(@Path("id") id: Int): retrofit2.Response<Unit>
}
