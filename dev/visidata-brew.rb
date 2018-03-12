class Visidata < Formula
  include Language::Python::Virtualenv
  desc "Terminal utility for exploring and arranging tabular data"
  homepage "http://visidata.org/"
  url "https://files.pythonhosted.org/packages/6f/ba/74e4a15d21c11a8d1941b61f87e64d5767e273ab1a366cab6b43f05f149b/visidata-1.1.tar.gz"
  sha256 "ae8b62f78ca30fc14695813694fea1d8b571b4a45efd61ced1ce1681e8edf36e"

  depends_on "python3"

  resource "six" do
    url "https://files.pythonhosted.org/packages/16/d8/bc6316cf98419719bd59c91742194c111b6f2e85abac88e496adefaf7afe/six-1.11.0.tar.gz"
    sha256 "70e8a77beed4562e7f14fe23a786b54f6296e34344c23bc42f07b15018ff98e9"
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/54/bb/f1db86504f7a49e1d9b9301531181b00a1c7325dc85a29160ee3eaa73a54/python-dateutil-2.6.1.tar.gz"
    sha256 "891c38b2a02f5bb1be3e4793866c8df49c7d19baabf9c1bad62547e0b4866aca"
  end

  def install
    venv = virtualenv_create(libexec, "python3")
    venv.pip_install resources
    venv.pip_install_and_link buildpath
    man1.install "visidata/man/vd.1"
  end

  test do
    (testpath/"test_visidata.sh").write <<~EOS
      #!/usr/bin/env bash
      curl -O https://raw.githubusercontent.com/saulpw/visidata/stable/tests/exp-digits.vd
      vd --play exp-digits.vd --batch --output results_test.tsv
    EOS
    chmod 0755, testpath/"test_visidata.sh"
    system "./test_visidata.sh"
    assert_predicate testpath/"results_test.tsv", :exist?
  end
end
