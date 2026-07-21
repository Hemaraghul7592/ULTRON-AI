package com.ultron.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.Memory
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Settings
import androidx.compose.ui.graphics.vector.ImageVector

sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    data object Splash : Screen("splash", "Splash", Icons.Default.Dashboard)
    data object Onboarding : Screen("onboarding", "Onboarding", Icons.Default.Dashboard)
    data object Chat : Screen("chat", "Chat", Icons.Default.Chat)
    data object Voice : Screen("voice", "Voice", Icons.Default.Mic)
    data object Memory : Screen("memory", "Memory", Icons.Default.Memory)
    data object Settings : Screen("settings", "Settings", Icons.Default.Settings)
    data object Dashboard : Screen("dashboard", "Dashboard", Icons.Default.Dashboard)
    data object ChatDetail : Screen("chat/{conversationId}", "Chat Detail", Icons.Default.Chat)
}

data class BottomNavItem(
    val screen: Screen,
    val label: String,
)

val bottomNavItems = listOf(
    BottomNavItem(Screen.Chat, "Chat"),
    BottomNavItem(Screen.Memory, "Memory"),
    BottomNavItem(Screen.Voice, "Voice"),
    BottomNavItem(Screen.Settings, "Settings"),
)
