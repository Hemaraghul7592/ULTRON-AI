package com.ultron.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.ultron.data.local.SettingsDataStore
import com.ultron.ui.components.UltronBottomNav
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
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var settingsDataStore: SettingsDataStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            var startOnBoarding by remember { mutableStateOf(true) }

            LaunchedEffect(Unit) {
                val onboardingComplete = settingsDataStore.onboardingComplete.first()
                startOnBoarding = !onboardingComplete
            }

            UltronTheme {
                UltronApp(startOnBoarding = startOnBoarding)
            }
        }
    }
}

@Composable
fun UltronApp(startOnBoarding: Boolean) {
    var showSplash by remember { mutableStateOf(true) }
    var showOnboarding by remember(startOnBoarding) { mutableStateOf(startOnBoarding) }

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
            UltronBottomNav(
                currentRoute = currentRoute,
                visible = showBottomBar,
                navController = navController,
            )
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
