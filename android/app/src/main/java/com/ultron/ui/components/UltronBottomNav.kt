package com.ultron.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavController
import androidx.navigation.NavGraph.Companion.findStartDestination
import com.ultron.ui.navigation.Screen

@Composable
fun UltronBottomNav(
    currentRoute: String?,
    visible: Boolean,
    navController: NavController,
    modifier: Modifier = Modifier,
) {
    AnimatedVisibility(
        visible = visible,
        enter = fadeIn(),
        exit = fadeOut(),
        modifier = modifier,
    ) {
        NavigationBar {
            NavigationBarItem(
                icon = { Icon(Screen.Chat.icon, contentDescription = "Chat") },
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
                icon = { Icon(Screen.Memory.icon, contentDescription = "Memory") },
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
                icon = { Icon(Screen.Voice.icon, contentDescription = "Voice") },
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
                icon = { Icon(Screen.Settings.icon, contentDescription = "Settings") },
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
}
