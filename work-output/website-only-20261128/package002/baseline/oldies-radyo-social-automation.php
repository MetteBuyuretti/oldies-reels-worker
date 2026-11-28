<?php
/**
 * Plugin Name:       Oldies Radyo Social & News Automation
 * Plugin URI:        https://oldiesradyo.com
 * Description:       Production-quality automated Instagram publishing, 3-scene Video/Reels engine, and Autonomous Multi-Source News Monitoring & Publishing for Oldies Radyo.
 * Version:           1.7.5
 * Requires at least: 6.0
 * Requires PHP:      8.1
 * Author:            Oldies Radyo
 * Author URI:        https://oldiesradyo.com
 * License:           GPL-2.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       oldies-radyo-social-automation
 * Domain Path:       /languages
 *
 * @package           OldiesRadyo\SocialAutomation
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

// Plugin constants
define('OLDIES_SOCIAL_VERSION', '1.7.5');
define('OLDIES_SOCIAL_DB_VERSION', '1.7.5');
define('OLDIES_SOCIAL_PLUGIN_FILE', __FILE__);
define('OLDIES_SOCIAL_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('OLDIES_SOCIAL_PLUGIN_URL', plugin_dir_url(__FILE__));
define('OLDIES_SOCIAL_DEFAULT_IG_USER_ID', '');
define('OLDIES_SOCIAL_DEFAULT_IG_USERNAME', 'oldiesradyo');
define('OLDIES_SOCIAL_API_HOST', 'https://graph.instagram.com');
define('OLDIES_SOCIAL_API_VERSION', 'v26.0');

// Load Autoloader
require_once OLDIES_SOCIAL_PLUGIN_DIR . 'includes/Autoloader.php';
\OldiesRadyo\SocialAutomation\Autoloader::register(OLDIES_SOCIAL_PLUGIN_DIR);

// Activation & Deactivation Hooks
register_activation_hook(__FILE__, [\OldiesRadyo\SocialAutomation\Plugin::class, 'activate']);
register_deactivation_hook(__FILE__, [\OldiesRadyo\SocialAutomation\Plugin::class, 'deactivate']);

// Initialize Plugin
add_action('plugins_loaded', function () {
    \OldiesRadyo\SocialAutomation\Plugin::getInstance()->init();
});
