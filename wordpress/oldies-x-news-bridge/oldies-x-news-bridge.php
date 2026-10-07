<?php
/**
 * Plugin Name: Oldies X News Bridge
 * Description: Approval-controlled X delivery over the existing Oldies editorial news queue.
 * Version: 0.1.0
 * Requires PHP: 8.0
 * Author: Oldies Radyo
 */
defined('ABSPATH') || exit;
require_once __DIR__ . '/includes/Policy.php';
require_once __DIR__ . '/includes/Store.php';
require_once __DIR__ . '/includes/Publisher.php';
require_once __DIR__ . '/includes/Controller.php';
add_action('plugins_loaded', [Oldies_X_News_Controller::class, 'boot'], 30);
