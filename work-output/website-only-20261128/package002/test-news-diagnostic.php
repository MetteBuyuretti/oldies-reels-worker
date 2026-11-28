<?php
declare(strict_types=1);
// Isolated candidate-only harness. No WordPress, network, cron or publishing.
namespace OldiesRadyo\SocialAutomation\News {
    class NewsCoordinator {
        public int $calls = 0;
        public bool $fail = false;
        public bool $skip = false;
        public function runScheduledCycle(): array {
            $this->calls++;
            if ($this->fail) { throw new \RuntimeException('SECRET_TOKEN https://private.invalid/?api_key=SECRET_KEY'); }
            return ['status' => $this->skip ? 'skipped' : 'success'];
        }
    }
}
namespace OldiesRadyo\SocialAutomation\Cron {
    $locks = []; $logs = [];
    function get_transient($key) { return $GLOBALS['test_locks'][$key] ?? false; }
    function set_transient($key, $value, $ttl) { $GLOBALS['test_locks'][$key] = $value; return true; }
    function delete_transient($key) { unset($GLOBALS['test_locks'][$key]); return true; }
    function error_log($message) { $GLOBALS['test_logs'][] = $message; return true; }
}
namespace {
    define('ABSPATH', __DIR__);
    require __DIR__ . '/candidate/src/Cron/Scheduler.php';
    use OldiesRadyo\SocialAutomation\Cron\Scheduler;
    use OldiesRadyo\SocialAutomation\News\NewsCoordinator;
    function verify(bool $ok, string $message): void {
        if (!$ok) { throw new \RuntimeException($message); }
    }
    function fixture(): array {
        $GLOBALS['test_locks'] = []; $GLOBALS['test_logs'] = [];
        $r = new \ReflectionClass(Scheduler::class);
        $s = $r->newInstanceWithoutConstructor();
        $c = new NewsCoordinator();
        $r->getProperty('newsCoordinator')->setValue($s, $c);
        return [$s, $c];
    }
    [$s,$c] = fixture();
    $GLOBALS['test_locks'][Scheduler::TRANSIENT_NEWS_LOCK] = 123;
    $s->handleNewsSourceCheckExecution();
    verify($c->calls === 0 && $GLOBALS['test_locks'][Scheduler::TRANSIENT_NEWS_LOCK] === 123 && !$GLOBALS['test_logs'], 'Existing lock must be preserved without execution.');
    echo "PASS 1 existing lock\n";
    [$s,$c] = fixture(); $s->handleNewsSourceCheckExecution();
    verify($c->calls === 1 && !$GLOBALS['test_locks'] && !$GLOBALS['test_logs'], 'Normal cycle must run once, release lock and not emit error.');
    echo "PASS 2 success\n";
    [$s,$c] = fixture(); $c->fail = true; $s->handleNewsSourceCheckExecution();
    $line = implode("\n", $GLOBALS['test_logs']);
    verify($c->calls === 1 && !$GLOBALS['test_locks'] && count($GLOBALS['test_logs']) === 1, 'Exception must be caught and lock cleared.');
    verify(str_contains($line, '[RuntimeException]') && !preg_match('/SECRET|https:|api_key|private.invalid/', $line), 'Exception message and credentials must never be logged.');
    echo "PASS 3 exception redaction and cleanup\n";
    [$s,$c] = fixture(); $c->skip = true; $s->handleNewsSourceCheckExecution();
    verify($c->calls === 1 && !$GLOBALS['test_locks'] && !$GLOBALS['test_logs'], 'Skipped coordinator result must not be changed into error or retried.');
    echo "PASS 4 skipped\n";
}
