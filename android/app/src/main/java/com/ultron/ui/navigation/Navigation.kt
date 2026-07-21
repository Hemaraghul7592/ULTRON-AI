package com.ultron.ui.navigation

import androidx.compose.ui.graphics.vector.ImageVector
import com.ultron.core.icon.UltronIcons

sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    data object Splash : Screen("splash", "Splash", UltronIcons.Dashboard)
    data object Onboarding : Screen("onboarding", "Onboarding", UltronIcons.Dashboard)
    data object Chat : Screen("chat", "Chat", UltronIcons.Chat)
    data object Voice : Screen("voice", "Voice", UltronIcons.Voice)
    data object Memory : Screen("memory", "Memory", UltronIcons.Memory)
    data object Settings : Screen("settings", "Settings", UltronIcons.Settings)
    data object Dashboard : Screen("dashboard", "Dashboard", UltronIcons.Dashboard)
}


