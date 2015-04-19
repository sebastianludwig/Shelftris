#encoding: utf-8

# call rake -T get a list of all invocable tasks
# call rake all=true -T to get all tasks
# call rake [all=true] -D to get a little bit more description

require 'time'
require 'rb-fsevent'

PI_HOSTNAME = "shelftris.local"
PI_USER = 'pi'
PYTHON = 'python3.4'

######

CLEAR_END_OF_LINE = "\033[K"

def sibling_path(*components)
    File.join(File.dirname(__FILE__), components)
end

def terminal_title(title)
    `/bin/bash -c 'echo -n -e \"\033]0;#{title}\007\" > /dev/tty'`
end

def remote_project_path
    "/home/pi/projects/#{File.basename(File.dirname(__FILE__))}"
end

def is_raspberry?
  `uname` == "Linux\n"
end

def backtick(command)
    command += " 2>&1"
    output = `#{command}`
    if output.include? 'Could not resolve hostname'
        puts "First attampt to resolve hostname failed - retry.."
        output = `#{command}`
        raise output if output.include? 'Could not resolve hostname'
    end
    return output
end

def ssh_command(command = '')
    ssh_command = "ssh #{PI_USER}@#{PI_HOSTNAME}"
    ssh_command += " '#{command}'" if command and !command.empty?
    ssh_command
end

def ssh_backtick(command)
    backtick(ssh_command(command))
end

namespace :remote do
    desc "Connect to the Raspberry via SSH"
    task :login do
        exec(ssh_command)
    end

    desc "Opens a remote desktop via VNC"
    task :vnc do
        backtick("open vnc://#{PI_HOSTNAME}:5901")
    end

    desc "Mounts the Raspberry user home directory as drive"
    task :mount do
        backtick("open afp://#{PI_USER}@#{PI_HOSTNAME}/Home\\ Directory")
    end

    desc "Unmounts the Raspberry user home directory"
    task :unmount do
        backtick("umount '/Volumes/Home Directory'") if `mount`.include? '/Volumes/Home Directory'
    end

    desc "Copy project files to the Raspberry. Uses the configured hostname by default, accepts the IP address as optional argument (rake 'remote:copy[192.168.0.70]')."
    task :copy, :destination do |t, args|
        args.with_defaults destination: PI_HOSTNAME
        excludes = %w(
            __pycache__
            include
            lib
            log
            *.img.gz
            .*
        ).map { |e| "--exclude '#{e}'" }
        command = "rsync -ar -e \"ssh -l #{PI_USER}\" --delete #{excludes.join(' ')} #{File.dirname(__FILE__)}/ #{args.destination}:#{remote_project_path}"
        backtick(command)
    end

    namespace :copy do
        desc "Like copy, but keeps watching for file modifications to copy the files again"
        task :watch => :copy do
            begin
                terminal_title "copy:watch"
                ip = nil

                fsevent = FSEvent.new
                options = {:latency => 5, :no_defer => true }
                fsevent.watch File.dirname(__FILE__), options do |directories|
                    puts "syncing..."
                    terminal_title "syncing..."
                    unless ip
                        parts = `ping -c 1 #{PI_HOSTNAME}`.split
                        if parts.size >= 3
                            md = parts[2].match(/(?:\d{0,3}\.){3}\d{0,3}/)
                            if md
                                ip = md[0]
                                puts "#{PI_HOSTNAME} IP resolved to #{ip}"
                            end
                        end
                    end

                    `rake -f #{__FILE__} "remote:copy[#{ip}]"`
                    puts "#{Time.now.strftime('%H:%M:%S')}: synced"
                    terminal_title "synced"
                    sleep(1)
                    terminal_title "copy:watch - #{Time.now.strftime('%H:%M:%S')}"
                end
                fsevent.run
            ensure
                terminal_title ""
            end
        end
    end

    desc "Reboots the Raspberry"
    task :reboot => :unmount do         # TODO support dependencies in remote_task
        ssh_backtick("sudo reboot")
    end

    desc "Shuts the Raspberry down."
    task :shutdown => :unmount do
        ssh_backtick("sudo shutdown -h now")
    end
end

namespace :backup do
    desc 'Creates a gzipped backup of the SD card. Accepts optional filname addition parameters (rake "backup:create[param1, param2]").'
    task :create do |t, args|
        puts `sudo diskutil list`
        puts "\nEnter disk number (dev/diskX): [2..n]"
        disk_number = STDIN.gets.strip.to_i
        raise "Disk number below 2 - probably wrong.." if disk_number < 2

        filename = ['sensationdriver', Time.now.strftime('%Y%m%d_%H%M')] + args.extras
        output_path = sibling_path(filename.join('_').gsub(' ', '_') + '.img.gz')

        puts `diskutil unmountDisk /dev/disk#{disk_number}`

        puts "Creating backup #{File.basename(output_path)} - this may take a while.. c[´]"

        puts `sudo dd bs=1M if=/dev/rdisk#{disk_number} | gzip > '#{output_path}'`

        puts "Finished: #{File.basename(output_path)} (#{'%.2f' % (File.size(output_path) / (1000.0 ** 3))} GB) - open in Finder? [y/n]"
        answer = STDIN.gets.strip
        `open #{File.dirname(output_path)}` if answer == 'y'
    end

    desc 'Restores a previously created backup.'
    task :restore do |t, args|
        backups = []
        Dir.chdir sibling_path do
            backups = Dir.glob('*.{img.gz,img}')
        end

        raise "No backups found in #{sibling_path}" if backups.empty?

        backups.each_with_index do |path, index|
            puts "#{index}\t#{path}"
        end
        puts
        puts "Choose backup to restore:"
        backup_path = backups[STDIN.gets.strip.to_i]
        puts

        puts `sudo diskutil list`
        puts "\nEnter disk number (dev/diskX): [2..n]"
        disk_number = STDIN.gets.strip.to_i
        raise "Disk number below 2 - probably wrong.." if disk_number < 2

        puts `diskutil unmountDisk /dev/disk#{disk_number}`

        puts "Restoring backup #{File.basename(backup_path)} - this may take a while.. c[´]"

        if File.extname(backup_path) == '.gz'
            puts `gzip -dc "#{backup_path}" | sudo dd bs=1M of=/dev/rdisk#{disk_number}`
        else
            puts `sudo dd bs=1M of=/dev/rdisk#{disk_number}`
        end

        puts "Finished"        
    end
end
