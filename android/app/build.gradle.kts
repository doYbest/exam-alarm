import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.kotlin.kapt)
    alias(libs.plugins.hilt)
}

android {
    namespace = "com.example.exambrief"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.exambrief"
        minSdk = 29
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
    buildTypes {
        getByName("debug") {
            buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000/\"")
            buildConfigField("String", "CLIENT_TOKEN", "\"local-debug-token-change-me\"")
        }
        getByName("release") {
            buildConfigField("String", "API_BASE_URL", "\"https://invalid.example/\"")
            buildConfigField("String", "CLIENT_TOKEN", "\"\"")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

kapt {
    correctErrorTypes = true
    arguments { arg("room.schemaLocation", "$projectDir/schemas") }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.okhttp)
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.hilt.viewmodel.compose)
    implementation(libs.androidx.work.runtime)
    implementation(libs.retrofit)
    implementation(libs.serialization.json)
    implementation(libs.hilt.android)
    kapt(libs.androidx.room.compiler)
    kapt(libs.hilt.compiler)
    testImplementation("junit:junit:4.13.2")
    debugImplementation(libs.androidx.compose.ui.tooling)
}
