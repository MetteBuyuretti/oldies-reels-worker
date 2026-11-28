<?php
declare(strict_types=1);

namespace OldiesRadyo\SocialAutomation\Cron {
    $GLOBALS['wp_filters'] = [];
    $GLOBALS['wp_scheduled_events'] = [];
    $GLOBALS['wp_cleared_hooks'] = [];
    $GLOBALS['wp_next_scheduled_map'] = [];

    function add_filter(string $hook, callable $callback): void {
        $GLOBALS['wp_filters'][$hook][] = $callback;
    }

    function apply_filters(string $hook, $value) {
        foreach ($GLOBALS['wp_filters'][$hook] ?? [] as $cb) {
            $value = $cb($value);
        }
        return $value;
    }

    function wp_next_scheduled(string $hook) {
        return $GLOBALS['wp_next_scheduled_map'][$hook] ?? false;
    }

    function wp_schedule_event(int $timestamp, string $recurrence, string $hook): bool {
        $defaultIntervals = [
            'hourly' => 3600,
            'daily'  => 86400,
        ];
        $resolved = apply_filters('cron_schedules', $defaultIntervals);
        if (!isset($resolved[$recurrence])) {
            throw new \RuntimeException("Missing recurrence interval: {$recurrence}");
        }
        $GLOBALS['wp_scheduled_events'][] = [
            'timestamp'  => $timestamp,
            'recurrence' => $recurrence,
            'hook'       => $hook,
        ];
        return true;
    }

    function wp_clear_scheduled_hook(string $hook): int {
        $GLOBALS['wp_cleared_hooks'][] = $hook;
        return 1;
    }
}

namespace {
    define('ABSPATH', __DIR__);
    require __DIR__ . '/candidate/src/Cron/Scheduler.php';

    use OldiesRadyo\SocialAutomation\Cron\Scheduler;

    final class TestScheduler extends Scheduler {
        public function rescheduleDailyPost(): void {
            // No-op in isolated news recurrence test; avoids real SettingsManager dependency.
        }
    }

    function assertTrue(bool $cond, string $msg): void {
        if (!$cond) {
            throw new \RuntimeException($msg);
        }
    }

    function makeFixture(bool $newsAlreadyScheduled): TestScheduler {
        $GLOBALS['wp_filters'] = [];
        $GLOBALS['wp_scheduled_events'] = [];
        $GLOBALS['wp_cleared_hooks'] = [];

        $future = time() + 600;
        $GLOBALS['wp_next_scheduled_map'] = [
            Scheduler::CRON_TOKEN_HEALTH          => $future,
            Scheduler::CRON_VIDEO_PERIODIC_CLEANUP => $future,
            Scheduler::CRON_RETENTION_CLEANUP      => $future,
            Scheduler::CRON_ETSY_PRODUCT_SYNC     => $future,
            Scheduler::CRON_NEWS_SOURCE_CHECK    => $newsAlreadyScheduled ? $future : false,
        ];

        $ref = new \ReflectionClass(Scheduler::class);
        /** @var TestScheduler $scheduler */
        $instanceRef = new \ReflectionClass(TestScheduler::class);
        $scheduler = $instanceRef->newInstanceWithoutConstructor();

        if ($ref->hasProperty('etsyProductSync')) {
            $prop = $ref->getProperty('etsyProductSync');
            $prop->setAccessible(true);
            $prop->setValue($scheduler, null);
        }

        return $scheduler;
    }

    // Test 1: Only news event is scheduled and only oldies_15_minutes interval is registered.
    $scheduler = makeFixture(false);
    $scheduler->scheduleDefaultEvents();

    $resolvedSchedules = \OldiesRadyo\SocialAutomation\Cron\apply_filters('cron_schedules', []);
    assertTrue(count($GLOBALS['wp_scheduled_events']) === 1, 'Expected exactly one wp_schedule_event call.');
    assertTrue(
        $GLOBALS['wp_scheduled_events'][0]['hook'] === Scheduler::CRON_NEWS_SOURCE_CHECK,
        'Scheduled event must be news source check hook.'
    );
    assertTrue(
        $GLOBALS['wp_scheduled_events'][0]['recurrence'] === 'oldies_15_minutes',
        'Scheduled recurrence must be oldies_15_minutes.'
    );
    assertTrue(isset($resolvedSchedules['oldies_15_minutes']), 'oldies_15_minutes must be registered.');
    assertTrue(!isset($resolvedSchedules['oldies_5_minutes']), 'oldies_5_minutes must not be registered.');
    echo "PASS 1 only news + 15m filter\n";

    // Test 2: Existing news event -> zero wp_schedule_event calls.
    $schedulerExisting = makeFixture(true);
    $schedulerExisting->scheduleDefaultEvents();

    assertTrue(
        count($GLOBALS['wp_scheduled_events']) === 0,
        'Existing news event must result in zero wp_schedule_event calls.'
    );
    echo "PASS 2 existing news no schedule call\n";
}
