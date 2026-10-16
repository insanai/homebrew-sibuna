# Generated from distribution/homebrew/sibuna.rb.in by distribution/scripts/homebrew_formula.py.
# It installs the release archives, the same executables the release workflow verified.
class Sibuna < Formula
  desc "Web firewall and anti-crawler proxy with proof-of-work admission"
  homepage "https://insanai.github.io/sibuna/"
  version "1.0.0-beta.2"
  license "LGPL-3.0-or-later"

  on_macos do
    on_arm do
      url "https://github.com/insanai/sibuna/releases/download/v1.0.0-beta.2/sibuna-macos-arm64.tar.gz"
      sha256 "e08ddb15cb3a38687decf110e3e873d16409a02a2e8aa7f2f89a0abe401221dd"
    end
    on_intel do
      url "https://github.com/insanai/sibuna/releases/download/v1.0.0-beta.2/sibuna-macos-amd64.tar.gz"
      sha256 "ed07da5cffd5593a80d068809530e3e23b7cded01383a7b80bb3fc05e8db72db"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/insanai/sibuna/releases/download/v1.0.0-beta.2/sibuna-linux-arm64.tar.gz"
      sha256 "8569788085b1551bcd11fe58f5194eb30818bb5cd60d521c4d08f82fb309cf78"
    end
    on_intel do
      url "https://github.com/insanai/sibuna/releases/download/v1.0.0-beta.2/sibuna-linux-amd64.tar.gz"
      sha256 "2b144a91a83eaf61d6d3f8e63701d31800ed6072dbc515f76e865234bb1857f7"
    end
  end

  def install
    bin.install "sibuna"
    doc.install "README.md", "SECURITY.md", "NOTICE", "sibuna.build.json", "LICENSES"
  end

  def caveats
    <<~EOS
      No service is started. Before running Sibuna, create a private admission seed of
      64 hexadecimal digits and pass it with --secret-file, with a persistent --data-dir:
        umask 077; od -An -tx1 -N32 /dev/urandom | tr -d ' \\n' > admission.seed
      Point --upstream-host (an IP literal) and --upstream-port at the origin.
      The console is opt-in; see https://insanai.github.io/sibuna/ for operations.
    EOS
  end

  test do
    assert_equal "sibuna #{version}", shell_output("#{bin}/sibuna --version 2>&1").strip
    require "net/http"
    require "timeout"
    seed = testpath/"admission.seed"
    seed.write Random.bytes(32).unpack1("H*")
    seed.chmod 0600
    original_seed = seed.read
    port = free_port
    2.times do
      pid = Process.spawn((bin/"sibuna").to_s, "--host", "127.0.0.1", "--port", port.to_s,
                          "--secret-file", seed.to_s, "--data-dir", (testpath/"state").to_s,
                          out: (testpath/"daemon.log").to_s, err: (testpath/"daemon.log").to_s)
      begin
        Timeout.timeout(30) do
          loop do
            begin
              response = Net::HTTP.get_response(URI("http://127.0.0.1:#{port}/__sibuna/health"))
              break if response.code == "200"
            rescue Errno::ECONNREFUSED, EOFError
              # The listener is still starting.
            end
            sleep 0.1
          end
        end
        assert_equal original_seed, seed.read
        assert_path_exists testpath/"state/sibuna.db"
      ensure
        Process.kill("TERM", pid)
        _, status = Process.wait2(pid)
      end
      assert_equal 0, status.exitstatus
    end
  end
end
