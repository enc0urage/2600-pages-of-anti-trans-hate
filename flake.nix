{
  description = "2600 pages of hate";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };
  outputs = {
    self,
    nixpkgs,
    utils,
  }:
    utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in rec {
        packages.default =
          pkgs.runCommand "2600-pages-of-anti-trans-hate" {}
          ''
            mkdir -p $out/
            ${packages.parser}/bin/parser ${packages.convert_to_text} $out
          '';
        packages.parser = pkgs.poetry2nix.mkPoetryApplication {
          projectDir = ./.;
        };
        packages.extract_attachments =
          pkgs.runCommand "attachments" {
            src = packages.download_torrent;
          } ''
            mkdir -p $out
            ${pkgs.poppler_utils}/bin/pdfdetach -saveall -o $out $src
          '';
        packages.convert_to_text =
          pkgs.runCommand "Emails.txt" {
            src = packages.download_torrent;
          } ''
            ${pkgs.poppler_utils}/bin/pdftotext -enc UTF-8 -eol unix -nopgbrk \
            $src $out;
          '';
        packages.download_torrent =
          pkgs.runCommand "Emails.pdf" {
            src = ./data/emails.torrent;
            outputHashAlgo = "sha256";
            outputHashMode = "flat";
            outputHash = "sha256-JPKTo18FLB5pxGjaM3klEALluJLgalah6pY95TONmu8=";
            preferLocalBuild = true;
          } ''
            ${pkgs.lftp}/bin/lftp -c "
            set torrent:seed-max-time 0
            set torrent:stop-on-ratio 0.0
            set torrent:use-dht true
            torrent $src
            wait all"
            mv 'the emails - 2600 pages of anti trans hate/Emails.pdf' $out
          '';
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [poetry];
        };
        formatter = pkgs.writeShellApplication {
          name = "treefmt-wrapped";
          runtimeInputs = with pkgs; [alejandra black];
          text = "${pkgs.treefmt}/bin/treefmt";
        };
      }
    );
}
