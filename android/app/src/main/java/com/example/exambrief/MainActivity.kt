package com.example.exambrief

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.example.exambrief.feature.hotspot.HotspotDetailScreen
import com.example.exambrief.feature.hotspot.HotspotHomeScreen
import com.example.exambrief.feature.alarm.AlarmScreen
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request

private val healthClient = OkHttpClient()
private val tabs = listOf("home" to "首页", "alarm" to "闹钟", "study" to "学习", "mine" to "我的")

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val colors = if (androidx.compose.foundation.isSystemInDarkTheme()) {
                darkColorScheme()
            } else {
                lightColorScheme()
            }
            MaterialTheme(colorScheme = colors) { AppNavigation() }
        }
    }
}

@Composable
private fun AppNavigation() {
    val navController = rememberNavController()
    val entry by navController.currentBackStackEntryAsState()
    val currentRoute = entry?.destination?.route
    Scaffold(
        bottomBar = {
            NavigationBar {
                tabs.forEach { (route, label) ->
                    NavigationBarItem(
                        selected = currentRoute == route,
                        onClick = {
                            navController.navigate(route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Text("●") },
                        label = { Text(label) },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(navController, startDestination = "home", modifier = Modifier.padding(padding)) {
            composable("home") {
                HotspotHomeScreen(onOpen = { id -> navController.navigate("detail/$id") })
            }
            composable("detail/{id}") { backStack ->
                HotspotDetailScreen(id = backStack.arguments?.getString("id").orEmpty())
            }
            composable("alarm") { AlarmScreen() }
            composable("study") { UnavailableScreen("学习功能正在开发") }
            composable("mine") {
                if (BuildConfig.DEBUG) HealthScreen() else UnavailableScreen("设置功能正在开发")
            }
        }
    }
}

@Composable
private fun UnavailableScreen(message: String) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) { Text(message) }
}

@Composable
private fun HealthScreen() {
    var health by remember { mutableStateOf("检查后端连接中…") }
    var refresh by remember { mutableIntStateOf(0) }
    LaunchedEffect(refresh) {
        health = withContext(Dispatchers.IO) {
            try {
                healthClient.newCall(
                    Request.Builder().url("http://10.0.2.2:8000/health").build()
                ).execute().use { response ->
                    if (response.isSuccessful) "后端连接正常" else "后端不可用：HTTP ${response.code}"
                }
            } catch (_: Exception) {
                "后端不可用，请检查本地服务"
            }
        }
    }
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("公考晨报 · 开发检查", style = MaterialTheme.typography.headlineSmall)
        Text(health, modifier = Modifier.padding(vertical = 16.dp))
        Button(onClick = { refresh++ }) { Text("重新检查") }
    }
}
