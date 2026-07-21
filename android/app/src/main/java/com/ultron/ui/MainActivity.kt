package com.ultron.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Memory
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.ultron.data.local.SettingsDataStore
import com.ultron.ui.navigation.Screen
import com.ultron.ui.screens.chat.ChatScreen
import com.ultron.ui.screens.dashboard.DashboardScreen
import com.ultron.ui.screens.memory.MemoryScreen
import com.ultron.ui.screens.onboarding.OnboardingScreen
import com.ultron.ui.screens.settings.SettingsScreen
import com.ultron.ui.screens.splash.SplashScreen
import com.ultron.ui.screens.voice.VoiceScreen
import com.ultron.ui.theme.UltronTheme
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var settingsDataStore: SettingsDataStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val onboardingComplete = runBlocking { settingsDataStore.onboardingComplete.first() }

        setContent {
            UltronTheme {
                UltronApp(startOnBoarding = !onboardingComplete)
            }
        }
    }
}

@Composable
fun UltronApp(startOnBoarding: Boolean) {
    val navController = rememberNavController()
    var showSplash by remember { mutableStateOf(true) }
    var showOnboarding by remember { mutableStateOf(startOnBoarding) }

    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay(2000)
        showSplash = false
    }

    when {
        showSplash -> {
            SplashScreen(onSplashComplete = { showSplash = false })
        }
        showOnboarding -> {
            OnboardingScreen(onComplete = { showOnboarding = false })
        }
        else -> {
            MainApp()
        }
    }
}

@Composable
fun MainApp() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val bottomBarRoutes = listOf(
        Screen.Chat.route,
        Screen.Memory.route,
        Screen.Voice.route,
        Screen.Settings.route,
    )
    val showBottomBar = currentRoute in bottomBarRoutes

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {
            AnimatedVisibility(
                visible = showBottomBar,
                enter = fadeIn(),
                exit = fadeOut(),
            ) {
                NavigationBar {
                    NavigationBarItem(
                        icon = { Icon(Icons.Default.Chat, contentDescription = "Chat") },
                        label = { Text("Chat") },
                        selected = currentRoute == Screen.Chat.route,
                        onClick = {
                            navController.navigate(Screen.Chat.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                    )
                    NavigationBarItem(
                        icon = { Icon(Icons.Default.Memory, contentDescription = "Memory") },
                        label = { Text("Memory") },
                        selected = currentRoute == Screen.Memory.route,
                        onClick = {
                            navController.navigate(Screen.Memory.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                    )
                    NavigationBarItem(
                        icon = { Icon(Icons.Default.Mic, contentDescription = "Voice") },
                        label = { Text("Voice") },
                        selected = currentRoute == Screen.Voice.route,
                        onClick = {
                            navController.navigate(Screen.Voice.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                    )
                    NavigationBarItem(
                        icon = { Icon(Icons.Default.Settings, contentDescription = "Settings") },
                        label = { Text("Settings") },
                        selected = currentRoute == Screen.Settings.route,
                        onClick = {
                            navController.navigate(Screen.Settings.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                    )
                }
            }
        },
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Chat.route,
            modifier = Modifier.padding(innerPadding),
        ) {
            composable(Screen.Chat.route) { ChatScreen() }
            composable(Screen.Memory.route) { MemoryScreen() }
            composable(Screen.Voice.route) { VoiceScreen() }
            composable(Screen.Settings.route) { SettingsScreen() }
            composable(Screen.Dashboard.route) { DashboardScreen() }
        }
    }
}
