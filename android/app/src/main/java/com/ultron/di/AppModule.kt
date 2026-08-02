package com.ultron.di

import android.content.Context
import androidx.room.Room
import com.ultron.BuildConfig
import com.ultron.data.local.AppDatabase
import com.ultron.data.local.ConversationDao
import com.ultron.data.local.MemoryDao
import com.ultron.data.local.MessageDao
import com.ultron.data.local.SettingsDataStore
import com.ultron.data.local.SecureTokenStore
import com.ultron.data.remote.ApiConfig
import com.ultron.data.remote.ApiService
import com.ultron.data.remote.AuthorizationInterceptor
import com.ultron.data.remote.SessionAuthenticator
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authorizationInterceptor: AuthorizationInterceptor,
        sessionAuthenticator: SessionAuthenticator,
    ): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC
            else HttpLoggingInterceptor.Level.NONE
        }
        return OkHttpClient.Builder()
            .addInterceptor(authorizationInterceptor)
            .addInterceptor(logging)
            .authenticator(sessionAuthenticator)
            .retryOnConnectionFailure(true)
            .connectTimeout(20, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(client: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl("${ApiConfig.validateBaseUrl(ApiConfig.DEFAULT_BASE_URL)}/${ApiConfig.API_PATH}")
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): ApiService {
        return retrofit.create(ApiService::class.java)
    }

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "ultron.db"
        )
            .addMigrations(AppDatabase.MIGRATION_1_2)
            .build()
    }

    @Provides
    fun provideConversationDao(db: AppDatabase): ConversationDao = db.conversationDao()

    @Provides
    fun provideMessageDao(db: AppDatabase): MessageDao = db.messageDao()

    @Provides
    fun provideMemoryDao(db: AppDatabase): MemoryDao = db.memoryDao()

    @Provides
    @Singleton
    fun provideSettingsDataStore(
        @ApplicationContext context: Context,
        secureTokenStore: SecureTokenStore,
    ): SettingsDataStore {
        return SettingsDataStore(context, secureTokenStore)
    }
}
